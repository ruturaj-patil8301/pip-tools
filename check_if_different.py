import pkg_resources
import sys
import os

def parse_requirements(file_path):
    requirements = {}
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and '==' in line:
                pkg, ver = line.split('==', 1)
                requirements[pkg.strip()] = ver.strip()
    return requirements

def get_installed_version(package_name):
    try:
        version = pkg_resources.get_distribution(package_name).version
        return version
    except pkg_resources.DistributionNotFound:
        return None

def compare_versions(requirements):
    mismatches = []
    for pkg, req_ver in requirements.items():
        inst_ver = get_installed_version(pkg)
        if inst_ver != req_ver:
            mismatches.append((pkg, req_ver, inst_ver or "Not Installed"))
    return mismatches

def main():
    if len(sys.argv) != 2:
        print("Usage: python check_installed_versions.py /path/to/requirements.txt")
        sys.exit(1)

    req_file = sys.argv[1]
    if not os.path.isfile(req_file):
        print(f"File not found: {req_file}")
        sys.exit(1)

    requirements = parse_requirements(req_file)
    mismatches = compare_versions(requirements)

    if mismatches:
        print("Packages with version mismatches:")
        print("{:<30} {:<20} {:<20}".format("Package", "Req. Version", "Installed Version"))
        print("-" * 70)
        for pkg, req_ver, inst_ver in mismatches:
            print("{:<30} {:<20} {:<20}".format(pkg, req_ver, inst_ver))
    else:
        print("All package versions match the installed versions.")

if __name__ == "__main__":
    main()
