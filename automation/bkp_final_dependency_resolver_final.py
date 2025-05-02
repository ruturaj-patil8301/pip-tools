import subprocess
import sys
import json
from packaging.version import Version, InvalidVersion
from packaging.specifiers import SpecifierSet

def run_pipdeptree(package_name):
    cmd = f'pipdeptree -p "{package_name}" --json 2>/dev/null'
    output = subprocess.check_output(cmd, shell=True, text=True)
    return json.loads(output)

def get_package_info(data, package_name):
    for package_entry in data:
        pkg = package_entry.get("package", {})
        if pkg.get("key").lower() == package_name.lower():
            return package_entry
    return None

def get_available_versions(package_name):
    """Use pip3 index versions to get list of available PyPI versions."""
    cmd = ["pip3", "index", "versions", package_name]
    output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
    versions = []
    for line in output.strip().splitlines():
        line = line.strip()
        if line.startswith('Available versions:'):
            line = line.replace('Available versions:', '').strip()
            versions = [v.strip() for v in line.split(',')]
    # Sort from oldest to newest explicitly (lowest first)
    try:
        versions = sorted(versions, key=Version)
    except InvalidVersion:
        pass
    return versions

def find_lowest_valid_version(package_name, version_specifier):
    """Given the version specifier, find the lowest PyPI available version explicitly meeting the specifier."""
    versions = get_available_versions(package_name)
    spec_set = SpecifierSet(version_specifier)

    for ver in versions:
        try:
            if Version(ver) in spec_set:
                return ver
        except InvalidVersion:
            continue
    # No matching version found explicitly
    return None

def main(package_name):
    data = run_pipdeptree(package_name)
    package_info = get_package_info(data, package_name)

    if not package_info:
        #print(f"Package '{package_name}' not found in pipdeptree output.")
        sys.exit(1)

    dependency_issues = []

    dependencies = package_info.get("dependencies", [])
    for dep in dependencies:
        dep_name = dep.get("package_name")
        installed_version = dep.get("installed_version")
        required_version_spec = dep.get("required_version", "").strip()

        # Explicitly skip missing packages as requested
        if installed_version == '?' or installed_version is None:
            #print(f"Skipping missing package '{dep_name}'.")
            continue

        # No specific version constraints ("Any" explicitly): always satisfied
        if required_version_spec.lower() == 'any' or required_version_spec == '':
            continue

        # Explicit check of dependency requirements
        try:
            #print(f"Dependency : {dep_name} Installed Version: {installed_version} required_version_spec: {required_version_spec}")
            if Version(installed_version) not in SpecifierSet(required_version_spec):
                # Explicitly find lowest valid PyPI version as per your request
                fixed_version = find_lowest_valid_version(dep_name, required_version_spec)
                if fixed_version:
                    dependency_issues.append(f"{dep_name}=={fixed_version}")
                else:
                    #print(f"No suitable version found for {dep_name} matching '{required_version_spec}'.")
        except Exception as e:
            #print(f"Error checking version for {dep_name}: {e}")

    #print("\nDependency issue packages (fixed to lowest satisfying versions):")
    print(dependency_issues)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <package_name>")
        sys.exit(1)

    package_name = sys.argv[1]
    main(package_name)
