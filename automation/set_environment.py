#!/usr/bin/env python3

import subprocess
import sys
import os
import logging
import traceback
import shutil

logging.basicConfig(
    filename='resolve_dependencies.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def run_subprocess(command, error_msg):
    try:
        subprocess.check_call(command, shell=True, executable='/bin/bash')
    except subprocess.CalledProcessError as e:
        logging.error(f"{error_msg}: {e}")
        raise

def ensure_system_package(package_name):
    logging.info(f"Checking if '{package_name}' is installed...")
    if shutil.which(package_name):
        logging.info(f"{package_name} already installed.")
        return
    logging.info(f"{package_name} not found. Installing now.")
    try:
        run_subprocess(f"sudo apt-get update && sudo apt-get install -y {package_name}",
                       f"Failed to install system package '{package_name}'")
    except Exception as e:
        logging.error(f"Unable to install system package '{package_name}': {e}")
        sys.exit(1)

def create_virtualenv(env_name):
    try:
        subprocess.check_call(["python3", "-m", "venv", env_name])
        logging.info(f"Virtual environment '{env_name}' created successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to create virtual environment '{env_name}': {e}")
        raise

def run_command_in_venv(command, env_path, step_desc):
    activate_env = f"source {env_path}/bin/activate"
    full_command = f"{activate_env} && {command}"
    logging.info(f"Starting step: {step_desc}")
    try:
        subprocess.check_call(full_command, shell=True, executable='/bin/bash')
        logging.info(f"Completed successfully: {step_desc}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed during '{step_desc}': {e}")
        raise

def main(requirement_file, yml_file):
    virtual_env_name = "demo_myenv"
    env_path = os.path.abspath(virtual_env_name)

    logging.info("--- Starting environment setup ---")

    # Step 0: Ensure python3-venv is installed
    ensure_system_package('python3-venv')

    # Create virtual environment explicitly
    try:
        create_virtualenv(virtual_env_name)
    except Exception:
        print("Error creating virtual environment. See resolve_dependencies.log for details.")
        sys.exit(1)

    # Step 1 (THE FIX): Install required packages explicitly WITHIN the virtual environment
    try:
        packages_to_install = 'pipdeptree pip-tools pyyaml pip-autoremove'
        run_command_in_venv(
            f"pip install {packages_to_install}",
            env_path,
            "Installing required python packages into virtual environment"
        )
    except Exception:
        print("Error installing base required pip packages in virtualenv. Check resolve_dependencies.log")
        sys.exit(1)

    # Step 2(a): Now safely run extract_install_pip_apt_from_yml.py
    try:
        run_command_in_venv(
            f"python extract_install_pip_apt_from_yml.py {yml_file}",
            env_path,
            "YML Pip & Apt package extraction and installation"
        )
    except Exception:
        print("Error during extraction and installation from yml. Check resolve_dependencies.log")
        sys.exit(1)

    # Step 2(b): Finally, run install_packages_from_requirement_files.sh
    try:
        run_command_in_venv(
            f"bash install_packages_from_requirement_files.sh {requirement_file}",
            env_path,
            "Requirements TXT package installation"
        )
    except Exception:
        print("Error during requirement packages installation. Check resolve_dependencies.log")
        sys.exit(1)

    logging.info("--- Environment setup completed successfully ---")
    print("\nSetup Finished Successfully!")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"\nUsage: python3 {sys.argv[0]} <requirement_file> <yml_file>\n")
        logging.error("Invalid usage. Insufficient arguments.")
        sys.exit(1)

    requirement_file, yml_file = sys.argv[1], sys.argv[2]

    for file_path in [requirement_file, yml_file]:
        if not os.path.isfile(file_path):
            msg = f"Required file not found: {file_path}"
            logging.error(msg)
            print(msg)
            sys.exit(1)

    try:
        main(requirement_file, yml_file)
    except Exception as e:
        logging.critical(f"Unexpected critical failure: {traceback.format_exc()}")
        print(f"Unexpected error: {str(e)} Refer 'resolve_dependencies.log' for details.")
        sys.exit(1)
