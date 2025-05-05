#!/usr/bin/env python3
import subprocess
import sys
import os
import logging
import traceback
import shutil

# Configure logging to write to a file with timestamp, level, and message
logging.basicConfig(
    filename='resolve_dependencies.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def run_subprocess(command, error_msg):
    """
    Execute a shell command and handle errors.
    
    Args:
        command (str): Shell command to execute
        error_msg (str): Error message to log if command fails
        
    Returns:
        None
        
    Raises:
        subprocess.CalledProcessError: If the command execution fails
        
    Logs:
        - ERROR: If command execution fails
    """
    try:
        subprocess.check_call(command, shell=True, executable='/bin/bash')
    except subprocess.CalledProcessError as e:
        logging.error(f"{error_msg}: {e}")
        raise

def ensure_system_package(package_name):
    """
    Check if a system package is installed and install it if not.
    
    Args:
        package_name (str): Name of the system package to check/install
        
    Returns:
        None
        
    Exits:
        - With code 1 if package installation fails
        
    Logs:
        - INFO: Package status (installed or not)
        - INFO: When installing a package
        - ERROR: If installation fails
    """
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
    """
    Create a Python virtual environment.
    
    Args:
        env_name (str): Name of the virtual environment to create
        
    Returns:
        None
        
    Raises:
        subprocess.CalledProcessError: If virtual environment creation fails
        
    Logs:
        - INFO: When virtual environment is created successfully
        - ERROR: If creation fails
    """
    try:
        subprocess.check_call(["python3", "-m", "venv", env_name])
        logging.info(f"Virtual environment '{env_name}' created successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to create virtual environment '{env_name}': {e}")
        raise

def run_command_in_venv(command, env_path, step_desc):
    """
    Run a command within a Python virtual environment.
    
    Args:
        command (str): Command to run in the virtual environment
        env_path (str): Path to the virtual environment
        step_desc (str): Description of the step being performed
        
    Returns:
        None
        
    Raises:
        subprocess.CalledProcessError: If command execution fails
        
    Logs:
        - INFO: When starting and completing a step
        - ERROR: If step execution fails
    """
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
    """
    Set up a Python virtual environment and install required packages.
    
    This function:
    1. Creates a virtual environment
    2. Installs base required packages
    3. Processes YAML configuration to install packages
    4. Installs packages from requirements file
    
    Args:
        requirement_file (str): Path to requirements file
        yml_file (str): Path to YAML configuration file
        
    Returns:
        None
        
    Exits:
        - With code 1 if any step fails
        
    Logs:
        - INFO: At the start and end of environment setup
        - ERROR: If any step fails
    """
    virtual_env_name = "demo_myenv"
    env_path = os.path.abspath(virtual_env_name)

    logging.info("--- Starting environment setup ---")

    # Step 0: Ensure python3-venv is installed
    ensure_system_package('python3-venv')

    # Create virtual environment explicitly
    try:
        create_virtualenv(virtual_env_name)
    except Exception:
        error_msg = "Error creating virtual environment. See resolve_dependencies.log for details."
        print(error_msg)
        logging.error(error_msg)  # Explicitly logging
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
        error_msg = "Error installing base required pip packages in virtualenv. Check resolve_dependencies.log"
        print(error_msg)
        logging.error(error_msg)  # Explicitly logging
        sys.exit(1)

    # Step 2(a): Now safely run extract_install_pip_apt_from_yml.py
    try:
        run_command_in_venv(
            f"python extract_install_pip_apt_from_yml.py {yml_file}",
            env_path,
            "YML Pip & Apt package extraction and installation"
        )
    except Exception:
        error_msg = "Error during extraction and installation from yml. Check resolve_dependencies.log"
        print(error_msg)
        logging.error(error_msg)  # Explicitly logging
        sys.exit(1)

    # Step 2(b): Finally, run install_packages_from_requirement_files.sh
    try:
        run_command_in_venv(
            f"bash install_packages_from_requirement_files.sh {requirement_file}",
            env_path,
            "Requirements.txt package installation"
        )
    except Exception:
        error_msg = "Error during requirement packages installation. Check resolve_dependencies.log"
        print(error_msg)
        logging.error(error_msg)  # Explicitly logging
        sys.exit(1)

    logging.info("--- Environment setup completed successfully ---")
    success_msg = "Setup Finished Successfully!"
    print("\n" + success_msg)
    logging.info(success_msg)  # Explicitly logging success message

if __name__ == "__main__":
    """
    Command-line interface for setting up a Python environment.
    
    Usage:
        python set_environment.py <requirement_file> <yml_file>
    
    Args:
        requirement_file: Path to the requirements file
        yml_file: Path to the YAML configuration file
    
    Exits:
        - With code 1 if arguments are missing or invalid
        - With code 1 if any required file is not found
        - With code 1 if an unexpected error occurs
    
    Logs:
        - ERROR: If arguments are missing or invalid
        - ERROR: If required files are not found
        - CRITICAL: If an unexpected error occurs
    """
    # Explicitly handling and logging the missing arguments scenario
    if len(sys.argv) != 3:
        usage_msg = f"\nUsage: python3 {sys.argv[0]} <requirement_file> <yml_file>\n"
        print(usage_msg)
        logging.error("Invalid usage: Insufficient arguments provided.")  # Explicitly logging
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
        critical_msg = f"Unexpected critical failure: {traceback.format_exc()}"
        logging.critical(critical_msg)
        print(f"Unexpected error: {str(e)} Refer 'resolve_dependencies.log' for details.")
        sys.exit(1)
