import subprocess
import sys
import json
import logging
from packaging.version import Version, InvalidVersion
from packaging.specifiers import SpecifierSet

logging.basicConfig(
    filename='resolve_dependencies.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def run_pipdeptree(package_name):
    cmd = f'pipdeptree -p "{package_name}" --json 2>/dev/null'
    try:
        output = subprocess.check_output(cmd, shell=True, text=True)
        return json.loads(output)
    except subprocess.CalledProcessError as e:
        logging.error(f"pipdeptree failed for package '{package_name}': {e}")
        return []

def get_package_info(data, package_name):
    for package_entry in data:
        pkg = package_entry.get("package", {})
        if pkg.get("key").lower() == package_name.lower():
            return package_entry
    return None

def get_available_versions(package_name):
    try:
        output = subprocess.check_output(["pip3", "index", "versions", package_name],
                                         text=True, stderr=subprocess.DEVNULL)
        versions = []
        for line in output.strip().splitlines():
            line = line.strip()
            if line.startswith('Available versions:'):
                line = line.replace('Available versions:', '').strip()
                versions = [v.strip() for v in line.split(',')]
        sorted_versions = sorted(versions, key=lambda v: Version(v))
        return sorted_versions
    except subprocess.CalledProcessError as e:
        logging.error(f"Error fetching versions for package '{package_name}': {e}")
        return []

def find_lowest_valid_version(package_name, version_specifier):
    versions = get_available_versions(package_name)
    specifier_set = SpecifierSet(version_specifier)

    for ver in versions:
        try:
            if Version(ver) in specifier_set:
                return ver
        except InvalidVersion:
            continue
    return None

def main(package_name):
    logging.info(f"[dependency_resolver_final.py] Analyzing dependencies explicitly for package '{package_name}'")

    data = run_pipdeptree(package_name)
    package_info = get_package_info(data, package_name)

    if not package_info:
        logging.error(f"No package info found for '{package_name}'. Exiting.")
        print("[]")
        sys.exit(1)

    dependency_issues = []

    dependencies = package_info.get("dependencies", [])
    for dep in dependencies:
        dep_name = dep.get("package_name")
        installed_version = dep.get("installed_version")
        required_version_spec = dep.get("required_version", "").strip()

        if installed_version == '?' or installed_version is None:
            logging.warning(f"Dependency '{dep_name}' is not installed. Skipping.")
            continue

        if required_version_spec.lower() == 'any' or required_version_spec == '':
            continue

        try:
            if Version(installed_version) not in SpecifierSet(required_version_spec):
                fixed_version = find_lowest_valid_version(dep_name, required_version_spec)
                if fixed_version:
                    dependency_issues.append(f"{dep_name}=={fixed_version}")
                    logging.info(f"Dependency issue: {dep_name} installed {installed_version} does not meet specifier {required_version_spec}. Fixed as {fixed_version}.")
                else:
                    logging.warning(f"No suitable version on PyPI found for dependency {dep_name} with specifier '{required_version_spec}'")
        except Exception as e:
            logging.error(f"Error processing dependency '{dep_name}': {e}")

    logging.info(f"Final problematic dependencies for '{package_name}': {dependency_issues}")
    print(json.dumps(dependency_issues))  # outputs valid JSON explicitly

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"\nUsage: python3 {sys.argv[0]} <package_name>\n")
        sys.exit(1)
    package_name = sys.argv[1].strip()

    try:
        main(package_name)
    except Exception as ex:
        logging.error(f"Unexpected error processing '{package_name}': {ex}", exc_info=True)
        print("[]")  # always output explicitly valid JSON even on error
        sys.exit(1)
