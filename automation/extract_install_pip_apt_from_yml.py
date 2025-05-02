import yaml
import subprocess
from pathlib import Path
import os
import sys

class PipPackage:
    def __init__(self, name, requirements_file=None):
        self.name = name
        self.requirements_file = requirements_file

class AptPackage:
    def __init__(self, name):
        self.name = name

def extract_packages(yaml_file_path):
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
                            requirements_file_path = pip_data['requirements']
                            requirements_packages = read_requirements_file(requirements_file_path)
                            for req_pkg in requirements_packages:
                                pip_packages.append(PipPackage(req_pkg))

                # Extract apt packages
                elif 'apt' in task:
                    apt_data = task['apt']

                    if isinstance(apt_data, dict):
                        names = apt_data.get('name', [])
                        if isinstance(names, str):
                            names = [names]

                        for name in names:
                            apt_packages.append(AptPackage(name))
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            return [], []

    return pip_packages, apt_packages

def read_requirements_file(requirements_file):
    """
    Read packages from the requirements file if it exists.
    """
    if os.path.exists(requirements_file):
        try:
            with open(requirements_file, 'r') as file:
                return [line.strip() for line in file if line.strip()]
        except IOError as e:
            print(f"Error reading requirements file {requirements_file}: {e}")
            return []
    else:
        print(f"Requirements file not found: {requirements_file}")
        return []

def install_pip_packages(packages):
    """
    Install pip packages using pip3 command.
    """
    for pkg in packages:
        try:
            print(f"Installing pip package: {pkg.name}")
            subprocess.run(["pip3", "install", pkg.name], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error installing {pkg.name}: {e}")

def install_apt_packages(packages):
    """
    Install apt packages using apt-get command.
    """
    try:
        print("Updating apt cache...")
        subprocess.run(["sudo", "apt-get", "update"], check=True)

        for pkg in packages:
            try:
                print(f"Installing apt package: {pkg.name}")
                subprocess.run(["sudo", "apt-get", "install", "-y", pkg.name], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error installing {pkg.name}: {e}")
    except subprocess.CalledProcessError as e:
        print(f"Error updating apt cache: {e}")

def main():
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <file.yml>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    pip_packages, apt_packages = extract_packages(file_path)

    if pip_packages:
        print(f"Pip packages found in {file_path}:\n")
        for pkg in pip_packages:
            print(f"Package: {pkg.name}")
        # Install pip packages
        install_pip_packages(pip_packages)
    else:
        print("No pip packages found.")

    if apt_packages:
        print(f"\nApt packages found in {file_path}:\n")
        for pkg in apt_packages:
            print(f"Package: {pkg.name}")
        # Install apt packages
        install_apt_packages(apt_packages)
    else:
        print("No apt packages found.")

if __name__ == '__main__':
    main()
