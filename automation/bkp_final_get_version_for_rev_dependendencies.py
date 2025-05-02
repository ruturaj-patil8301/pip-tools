import subprocess
import sys
from packaging.version import Version, InvalidVersion

def get_available_versions(package_name):
    """
    Fetch available versions from PyPI using pip3.
    Returns a sorted list of version strings (ascending).
    """
    try:
        output = subprocess.check_output(["pip3", "index", "versions", package_name],
                                         text=True,
                                         stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        sys.exit(1)

    versions = []
    for line in output.strip().splitlines():
        line = line.strip()
        if line.startswith('Available versions:'):
            line = line.replace('Available versions:', '').strip()
            versions = [v.strip() for v in line.split(',')]
    
    return sorted(versions, key=Version)

def main(package_name, input_version, flags):
    versions = get_available_versions(package_name)
    input_ver = Version(input_version)

    higher_versions = [v for v in versions if Version(v) > input_ver]

    if not higher_versions:
        sys.exit(0)  # No output, explicitly as per instructions

    outputs = []

    first_higher_version = higher_versions[0]
    latest_version = higher_versions[-1]
    first_idx = versions.index(higher_versions[0])
    last_idx = versions.index(higher_versions[-1])
    trail_idx = (first_idx + last_idx) // 2
    trail_version = versions[trail_idx]

    # Explicitly printing only requested outputs according to flags
    if '--first' in flags:
        print(higher_versions[0])

    if '--latest' in flags:
        print(higher_versions[-1])

    if '--trail' in flags:
        print(trail_version)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(f"Usage: python3 {sys.argv[0]} <package_name> <input_version> [--first] [--latest] [--trail]")
        sys.exit(1)

    package_name, input_version = sys.argv[1], sys.argv[2]
    flags = sys.argv[3:]

    main(package_name, input_version, flags)
