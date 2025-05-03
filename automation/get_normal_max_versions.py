import yaml
import sys
import logging
from packaging.version import Version

# Logging explicitly to the file
logging.basicConfig(
    filename='resolve_dependencies.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_config(config_file):
    logging.info(f"Loading configuration explicitly from: {config_file}")
    try:
        with open(config_file, 'r') as stream:
            return yaml.safe_load(stream)
    except Exception as e:
        logging.error(f"Error loading config file '{config_file}': {e}")
        return None

def read_requirements(file_path):
    packages = {}
    try:
        with open(file_path, 'r') as fp:
            logging.info(f"Reading requirements from: {file_path}")
            for line in fp:
                line = line.strip()
                if line and '==' in line:
                    pkg, ver = line.split('==')
                    packages[pkg.strip()] = ver.strip()
    except FileNotFoundError:
        logging.error(f"File not found explicitly: {file_path}")
    except Exception as e:
        logging.error(f"Error reading from {file_path}: {e}")
    return packages

def write_requirements(file_path, package_versions):
    try:
        with open(file_path, 'w') as fp:
            logging.info(f"Writing explicitly updated requirements to: {file_path}")
            for pkg, ver in package_versions.items():
                fp.write(f"{pkg}=={ver}\n")
    except Exception as e:
        logging.error(f"Error writing requirements to '{file_path}': {e}")

def get_package_version(file, package_name):
    packages = read_requirements(file)
    package_name_lower = package_name.lower()
    packages_lower = {pkg.lower(): ver for pkg, ver in packages.items()}

    version = packages_lower.get(package_name_lower)
    if version:
        logging.info(f"Found {package_name} version in {file}: {version}")
    else:
        logging.warning(f"{package_name} not found in {file}")
    return version

def get_max_version_across_files(files, package_name):
    package_name_lower = package_name.lower()
    max_version = None
    file_with_max_version = None

    for file in files:
        packages = read_requirements(file)
        packages_lower = {pkg.lower(): ver for pkg, ver in packages.items()}

        ver = packages_lower.get(package_name_lower)
        if ver:
            try:
                current_version = Version(ver)
                if not max_version or current_version > Version(max_version):
                    max_version = ver
                    file_with_max_version = file
            except Exception as e:
                logging.error(f"Invalid version format for {package_name} in {file}: {ver} - {e}")

    if max_version:
        logging.info(f"Max version of {package_name} across files: {max_version} found in {file_with_max_version}")
        return [max_version, file_with_max_version]
    else:
        logging.warning(f"{package_name} not found in any files.")
        return [None, None]

def update_package_version_in_file(file, package_name, new_version):
    package_name_lower = package_name.lower()
    updated = False

    try:
        with open(file, 'r') as fp:
            lines = fp.readlines()

        with open(file, 'w') as fp:
            for line in lines:
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith('#') and '==' in line_stripped:
                    pkg, ver = line_stripped.split('==', 1)
                    if pkg.strip().lower() == package_name_lower:
                        line = f"{pkg.strip()}=={new_version}\n"
                        updated = True
                        logging.info(f"Updating {package_name} from {ver.strip()} to {new_version} explicitly in {file}")

                fp.write(line)

        if updated:
            logging.info(f"Successfully updated {package_name} to version {new_version} explicitly in {file}")
            return True
        else:
            logging.warning(f"{package_name} not found explicitly in {file}; no update made.")
            return False

    except Exception as e:
        logging.error(f"Error while updating requirements file '{file}': {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logging.error("No action provided. Exiting explicitly.")
        sys.exit(1)

    config = load_config("files_config.yml")
    if not config:
        logging.error("Configuration loading failed explicitly. Exiting.")
        sys.exit(1)

    files = config.get('requirement_files', [])
    action = sys.argv[1]

    if action == "get":
        if len(sys.argv) != 4:
            logging.error("Incorrect usage clearly for 'get'.")
            sys.exit(1)
        _, _, package_name, file = sys.argv
        version = get_package_version(file, package_name)
        if version:
            print(version)  # Only explicitly the version number here
        else:
            sys.exit(1)

    elif action == "max":
        if len(sys.argv) != 3:
            logging.error("Incorrect usage clearly for 'max'.")
            sys.exit(1)
        _, _, package_name = sys.argv
        max_ver, found_file = get_max_version_across_files(files, package_name)
        if max_ver and found_file:
            print([max_ver, found_file])  # Clearly usable Python literal
        else:
            sys.exit(1)

    elif action == "set":
        if len(sys.argv) != 5:
            logging.error("Incorrect usage clearly for 'set'.")
            sys.exit(1)
        _, _, package_name, new_version, file = sys.argv
        success = update_package_version_in_file(file, package_name, new_version)
        if not success:
            sys.exit(1)

    else:
        logging.error(f"Invalid action '{action}' specified explicitly; exiting explicitly.")
        sys.exit(1)
