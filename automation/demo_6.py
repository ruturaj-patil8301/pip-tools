import yaml
import sys
import logging
from packaging.version import Version

# Set up explicit logging:
logging.basicConfig(
    filename='resolve_dependencies.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_config(config_file):
    with open(config_file, 'r') as stream:
        logging.info(f"Loading config file: {config_file}")
        return yaml.safe_load(stream)

def read_requirements(file_path):
    packages = {}
    try:
        with open(file_path, 'r') as fp:
            logging.info(f"Reading requirements from: {file_path}")
            for line in fp:
                line = line.strip()
                if '==' in line:
                    pkg, ver = line.split('==')
                    packages[pkg.strip()] = ver.strip()
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
    return packages

def write_requirements(file_path, package_versions):
    with open(file_path, 'w') as fp:
        logging.info(f"Writing updated requirements to: {file_path}")
        for pkg, ver in package_versions.items():
            fp.write(f"{pkg}=={ver}\n")

def get_package_version(file, package_name):
    packages = read_requirements(file)
    version = packages.get(package_name)
    if version:
        logging.info(f"{package_name} version in {file}: {version}")
    else:
        logging.warning(f"{package_name} not found in {file}")
    return version

def get_max_version_across_files(files, package_name):
    max_version = None
    file_with_max_version = None
    for file in files:
        packages = read_requirements(file)
        ver = packages.get(package_name)
        if ver:
            try:
                current_version = Version(ver)
                if (max_version is None) or (current_version > Version(max_version)):
                    max_version = ver
                    file_with_max_version = file
            except Exception as e:
                logging.error(f"Version parsing error for {package_name} in {file}: {e}")
    if max_version:
        logging.info(f"Max version of {package_name} across files: {max_version} (found in {file_with_max_version})")
        return [max_version, file_with_max_version]
    else:
        logging.warning(f"{package_name} not found in any files")
        return [None, None]

def update_package_version_in_file(file, package_name, new_version):
    packages = read_requirements(file)
    if package_name in packages:
        packages[package_name] = new_version
        write_requirements(file, packages)
        logging.info(f"Updated {package_name} to version {new_version} in {file}")
        return True
    logging.warning(f"No changes: {package_name} not found in {file}")
    return False

if __name__ == "__main__":
    config = load_config("files_config.yml")
    files = config['requirement_files']

    if len(sys.argv) < 2:
        logging.error("No action provided. Exiting.")
        sys.exit(1)

    action = sys.argv[1]

    if action == "get":
        if len(sys.argv) != 4:
            logging.error("Incorrect usage for 'get' command.")
            sys.exit(1)
        _, _, package_name, file = sys.argv
        version = get_package_version(file, package_name)
        if version:
            print(version)  # ONLY the version to stdout for 'get' action
        else:
            sys.exit(1)

    elif action == "max":
        if len(sys.argv) != 3:
            logging.error("Incorrect usage for 'max' command.")
            sys.exit(1)
        _, _, package_name = sys.argv
        result = get_max_version_across_files(files, package_name)
        if result[0]:
            print(result)  # print explicitly the list [max_version, file_with_max_version]
        else:
            sys.exit(1)

    elif action == "set":
        if len(sys.argv) != 5:
            logging.error("Incorrect usage for 'set' command.")
            sys.exit(1)
        _, _, package_name, new_version, file = sys.argv
        successful = update_package_version_in_file(file, package_name, new_version)
        if not successful:
            sys.exit(1)

    else:
        logging.error(f"Invalid action specified: {action}. Allowed actions: get|max|set")
        sys.exit(1)
