import yaml
import subprocess
from pathlib import Path
import os
import sys
import logging
import re
import json

# Configure logging to write to a file with timestamp, level, and message
logging.basicConfig(
    filename='resolve_dependencies.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class PipPackage:
    """
    Class representing a Python package to be installed via pip.
    
    Attributes:
        name (str): Name of the package
        requirements_file (str, optional): Path to requirements file containing the package
    """
    def __init__(self, name, requirements_file=None):
        self.name = name
        self.requirements_file = requirements_file

class AptPackage:
    """
    Class representing a system package to be installed via apt.
    
    Attributes:
        name (str): Name of the package
    """
    def __init__(self, name):
        self.name = name

def extract_packages(yaml_file_path):
    """
    Extract pip and apt packages from a YAML file.
    
    Args:
        yaml_file_path (str): Path to the YAML file
        
    Returns:
        tuple: (pip_packages, apt_packages) where each is a list of package objects
        
    Logs:
        - ERROR: If YAML parsing fails
        
    Note:
        - Handles both single package names and lists of package names
        - Processes requirements files referenced in the YAML
    """
    pip_packages = []
    apt_packages = []
    with open(yaml_file_path, 'r') as file:
        try:
            yaml_content = yaml.safe_load(file)
            for task in yaml_content:
                if not isinstance(task, dict):
                    continue
                
                # Extract pip packages
                if 'pip' in task:
                    pip_data = task['pip']
                    if isinstance(pip_data, dict):
                        if isinstance(pip_data.get('name'), str):
                            names = [pip_data['name']]
                        else:
                            names = pip_data.get('name', [])
                        for name in names:
                            pip_packages.append(PipPackage(name))
                        if 'requirements' in pip_data:
                            req_file_path = pip_data['requirements']
                            req_packages = read_requirements_file(req_file_path)
                            for req_pkg in req_packages:
                                pip_packages.append(PipPackage(req_pkg))
                
                # Extract apt packages
                if 'apt' in task:
                    apt_data = task['apt']
                    if isinstance(apt_data, dict):
                        names = apt_data.get('name', [])
                        if isinstance(names, str):
                            names = [names]
                        for name in names:
                            apt_packages.append(AptPackage(name))

        except yaml.YAMLError as e:
            logging.error(f"YAML parsing error in {yaml_file_path}: {e}")
            print(f"Error parsing YAML file: {e}")
    return pip_packages, apt_packages

def read_requirements_file(requirements_file):
    """
    Read packages from a requirements file.
    
    Args:
        requirements_file (str): Path to the requirements file
        
    Returns:
        list: List of package specifications from the file
        
    Logs:
        - ERROR: If file reading fails
        - WARNING: If file is not found
        
    Note:
        Returns only non-empty lines from the file
    """
    if os.path.exists(requirements_file):
        try:
            with open(requirements_file, 'r') as file:
                return [line.strip() for line in file if line.strip()]
        except IOError as e:
            logging.error(f"Error reading requirements file {requirements_file}: {e}")
            print(f"Error reading requirements file {requirements_file}: {e}")
    else:
        msg = f"Requirements file not found: {requirements_file}"
        logging.warning(msg)
        print(msg)
    return []

def install_pip_packages(packages):
    """
    Install Python packages using pip.
    
    Args:
        packages (list): List of PipPackage objects to install
        
    Logs:
        - INFO: When installing a package
        - ERROR: If installation fails
        
    Note:
        Uses pip3 to install packages
    """
    for pkg in packages:
        try:
            msg = f"Installing pip package: {pkg.name}"
            print(msg)
            logging.info(msg)
            subprocess.run(["pip3", "install", pkg.name], check=True)
        except subprocess.CalledProcessError as e:
            msg = f"Error installing pip package {pkg.name}: {e}"
            logging.error(msg)
            print(msg)

def install_apt_packages(packages):
    """
    Install system packages using apt-get.
    
    Args:
        packages (list): List of AptPackage objects to install
        
    Logs:
        - INFO: When updating apt cache and installing packages
        - ERROR: If apt update or installation fails
        
    Note:
        Updates apt cache before installing packages
    """
    try:
        logging.info("Updating apt cache.")
        print("Updating apt cache...")
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        for pkg in packages:
            try:
                msg = f"Installing apt package: {pkg.name}"
                print(msg)
                logging.info(msg)
                subprocess.run(["sudo", "apt-get", "install", "-y", pkg.name], check=True)
            except subprocess.CalledProcessError as e:
                msg = f"Error installing apt package {pkg.name}: {e}"
                logging.error(msg)
                print(msg)
    except subprocess.CalledProcessError as e:
        msg = f"Error updating apt cache: {e}"
        logging.error(msg)
        print(msg)

def set_package_version(pkg_name, new_version, file_path):
    """
    Update the version of a package in a YAML or requirements file.
    
    Args:
        pkg_name (str): Name of the package to update
        new_version (str): New version to set
        file_path (str): Path to the file to update
        
    Returns:
        dict: Result of the operation with status and details
        
    Logs:
        - INFO: When package is updated or already at desired version
        - WARNING: When package is not found
        - ERROR: When file is not found or an error occurs
        
    Note:
        - Uses case-insensitive regex to match package names
        - Handles different formats of package specifications in YAML files
        - Preserves the original case of the package name
    """
    try:
        if not Path(file_path).exists():
            msg = f"File not found: {file_path}"
            logging.error(msg)
            print(msg)
            return {"status": "error", "message": msg}
        
        with open(file_path, 'r') as file:
            lines = file.readlines()
    
        # Case-insensitive regex patterns to match different formats:
        # 1. For list items: "  - package==version"
        # 2. For single string: "  name: package==version"
        list_item_regex = re.compile(rf'^(\s*-\s+)({re.escape(pkg_name)})=='
                                    rf'([^\s]+)(.*)$', re.IGNORECASE)
        single_item_regex = re.compile(rf'^(\s*name:\s+)({re.escape(pkg_name)})=='
                                      rf'([^\s]+)(.*)$', re.IGNORECASE)
        
        updated = False
        package_found = False
        old_version = None

        for idx, line in enumerate(lines):
            # Try both patterns
            list_match = list_item_regex.match(line)
            single_match = single_item_regex.match(line)
            
            if list_match:
                package_found = True
                prefix, package_as_written, old_version, suffix = list_match.groups()
                if old_version != new_version:
                    # Use the original case of the package name from the file
                    new_line = f"{prefix}{package_as_written}=={new_version}{suffix}\n"
                    lines[idx] = new_line
                    updated = True
                    logging.info(f"Changing line from '{line.strip()}' to '{new_line.strip()}'")
            
            elif single_match:
                package_found = True
                prefix, package_as_written, old_version, suffix = single_match.groups()
                if old_version != new_version:
                    # Use the original case of the package name from the file
                    new_line = f"{prefix}{package_as_written}=={new_version}{suffix}\n"
                    lines[idx] = new_line
                    updated = True
                    logging.info(f"Changing line from '{line.strip()}' to '{new_line.strip()}'")

        if updated:
            with open(file_path, 'w') as file:
                file.writelines(lines)
            msg = f"Updated '{pkg_name}' to version '{new_version}' in {file_path}"
            logging.info(msg)
            print(msg)
            return {
                "status": "updated", 
                "message": msg,
                "package": pkg_name,
                "old_version": old_version,
                "new_version": new_version,
                "file": file_path
            }
        elif package_found:
            msg = f"'{pkg_name}' already at desired version '{new_version}' in {file_path}"
            logging.info(msg)
            print(msg)
            return {
                "status": "unchanged", 
                "message": msg,
                "package": pkg_name,
                "version": new_version,
                "file": file_path
            }
        else:
            msg = f"No package '{pkg_name}' found in {file_path} (case-insensitive search)"
            logging.warning(msg)
            print(msg)
            return {
                "status": "not_found", 
                "message": msg,
                "package": pkg_name,
                "file": file_path
            }

    except Exception as e:
        msg = f"Error updating '{pkg_name}' in {file_path}: {e}"
        logging.error(msg)
        print(msg)
        return {"status": "error", "message": msg, "package": pkg_name, "file": file_path}

def main():
    """
    Main function to extract and install packages from YAML files or update package versions.
    
    Usage modes:
    1. Extract and install: python script.py <file.yml>
    2. Set package version: python script.py set <pkg_name> <new_version> <file_path>
    
    Returns:
        None
        
    Exits:
        - With code 0 if successful
        - With code 1 if an error occurs
        
    Logs:
        - ERROR: If arguments are invalid or required files are not found
        - INFO: Package extraction and installation progress
    """
    if len(sys.argv) == 5 and sys.argv[1] == 'set':
        pkg_name, new_version, file_path = sys.argv[2], sys.argv[3], sys.argv[4]
        if not Path(file_path).exists():
            msg = f"File not found: {file_path}"
            print(msg)
            logging.error(msg)
            result = {"status": "error", "message": msg}
            print(f"RESULT: {json.dumps(result)}")
            sys.exit(1)
        result = set_package_version(pkg_name, new_version, file_path)
        # Print a special marker line that can be easily parsed by other scripts
        print(f"RESULT: {json.dumps(result)}")
        if result["status"] in ["updated", "unchanged"]:
            sys.exit(0)
        else:
            sys.exit(1)

    if len(sys.argv) != 2:
        msg = f"Usage: python3 {sys.argv[0]} <file.yml>"
        print(msg)
        logging.error(msg)
        sys.exit(1)

    yaml_file = sys.argv[1]
    if not Path(yaml_file).exists():
        msg = f"YAML file not found: {yaml_file}"
        print(msg)
        logging.error(msg)
        sys.exit(1)

    pip_packages, apt_packages = extract_packages(yaml_file)

    if pip_packages:
        print(f"\nPip packages found in {yaml_file}:\n")
        logging.info(f"Pip packages detected in {yaml_file}:")
        for pkg in pip_packages:
            print(f"Package: {pkg.name}")
            logging.info(f"Package: {pkg.name}")
        install_pip_packages(pip_packages)
    else:
        msg = "No pip packages found."
        print(msg)
        logging.info(msg)

    if apt_packages:
        print(f"\nApt packages found in {yaml_file}:\n")
        logging.info(f"Apt packages detected in {yaml_file}:")
        for pkg in apt_packages:
            print(f"Package: {pkg.name}")
            logging.info(f"Package: {pkg.name}")
        install_apt_packages(apt_packages)
    else:
        msg = "No apt packages found."
        print(msg)
        logging.info(msg)

if __name__ == '__main__':
    main()
