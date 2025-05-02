import subprocess
import sys
import logging
from packaging.version import Version, InvalidVersion

# Unified logging (appending to existing log file)
logging.basicConfig(
    filename='resolve_dependencies.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_available_versions(package_name):
    """Fetch available versions from PyPI using pip3 explicitly (without lambda)."""
    try:
        output = subprocess.check_output(
            ["pip3", "index", "versions", package_name],
            text=True, stderr=subprocess.DEVNULL
        )
        versions = []
        for line in output.strip().splitlines():
            line = line.strip()
            if line.startswith('Available versions:'):
                line = line.replace('Available versions:', '').strip()
                version_list = line.split(',')
                for v in version_list:
                    ver_clean = v.strip()
                    try:
                        Version(ver_clean)  # explicit valid version check
                        versions.append(ver_clean)
                    except InvalidVersion as e:
                        logging.error(f"Invalid version '{ver}' skipped for '{package_name}': {e}")
                break
        versions.sort(key=Version)
        return versions
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to get available versions for '{package_name}': {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error fetching versions for '{package_name}': {e}")
        return []

def main(package_name, input_version, flags):
    logging.info(f"Checking available versions for '{package_name}' greater than '{input_version}'")

    versions = get_available_versions(package_name)
    if not versions:
        logging.error(f"No available versions found explicitly for '{package_name}'.")
        sys.exit(1)

    try:
        input_ver = Version(input_version)
    except InvalidVersion as e:
        logging.error(f"Invalid input version '{input_version}' for package '{package_name}': {e}")
        sys.exit(1)

    higher_versions = [v for v in versions if Version(v) > input_ver]

    if not higher_versions:
        logging.info(f"No higher versions than '{input_version}' available explicitly for '{package_name}'. Nothing to do.")
        sys.exit(0)

    first_higher_version = higher_versions[0]
    latest_version = higher_versions[-1]

    first_index = versions.index(first_higher_version)
    latest_index = versions.index(latest_version)
    trail_index = (first_index + latest_index) // 2
    trail_version = versions[trail_index]

    if '--first' in flags:
        logging.info(f"Package '{package_name}': first higher version after '{input_version}' -> '{first_higher_version}'.")
        print(first_higher_version)

    if '--latest' in flags:
        logging.info(f"Latest version after '{input_version}' for '{package_name}': {latest_version}")
        print(latest_version)

    if '--trail' in flags:
        logging.info(f"Trail version for '{package_name}' after '{input_version}': {trail_version}")
        print(trail_version)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        logging.error(f"Incorrect usage. Provided arguments: {sys.argv}")
        print(f"Usage: python3 {sys.argv[0]} <package_name> <input_version> [--first] [--latest] [--trail]")
        sys.exit(1)

    package_name = sys.argv[1]
    input_version = sys.argv[2]
    flags = sys.argv[3:]

    try:
        main(package_name, input_version, flags)
    except Exception as e:
        logging.exception(f"Unhandled exception for '{package_name}' {input_version}: {e}")
        sys.exit(1)