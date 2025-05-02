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
        print(f"Package '{package_name}' not found or pip3 error.")
        sys.exit(1)

    versions = []
    for line in output.strip().splitlines():
        line = line.strip()
        if line.startswith('Available versions:'):
            line = line.replace('Available versions:', '').strip()
            for ver in line.split(','):
                ver_clean = ver.strip()
                try:
                    Version(ver_clean)  # validate version
                    versions.append(ver_clean)
                except InvalidVersion:
                    continue
    # sorted ascending (earlier versions first, latest version last)
    return sorted(versions, key=lambda x: Version(x))

def main(package_name, input_version):
    versions = get_available_versions(package_name)
    input_ver = Version(input_version)

    # Get versions greater than input_version
    higher_versions = [v for v in versions if Version(v) > input_ver]

    print(f"\nVersions greater than {input_version}:")
    if higher_versions:
        for v in higher_versions:
            print(v)
    else:
        print("None found.")
        print("\nCannot calculate trail version (no versions greater than input).")
        sys.exit(0)

    # trail version calculation using indexes
    first_idx = versions.index(higher_versions[0])
    last_idx = versions.index(higher_versions[-1])
    trail_idx = (first_idx + last_idx) // 2
    trail_version = versions[trail_idx]

    print(f"\nFirst version after {input_version}: {versions[first_idx]} (index {first_idx})")
    print(f"Latest available version: {versions[last_idx]} (index {last_idx})")
    print(f"\nCalculated trail version (mid-index method): {trail_version} (index {trail_idx})")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python3 {sys.argv[0]} <package_name> <input_version>")
        sys.exit(1)

    package_name, input_version = sys.argv[1], sys.argv[2]
    main(package_name, input_version)
