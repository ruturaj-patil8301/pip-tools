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
        logging.error(f"pipdeptree failed for package '{package_name}': {e.output}")
        return []

def get_package_info(data, package_name):
    for entry in data:
        pkg_key = entry.get("package", {}).get("key", "").lower()
        if pkg_key == package_name.lower():
            return entry
    return None

def get_available_versions(package_name):
    try:
        output = subprocess.check_output(["pip3", "index", "versions", package_name], text=True, stderr=subprocess.DEVNULL)
        versions = []
        for line in output.strip().splitlines():
            if line.startswith('Available versions:'):
                versions_line = line.split('Available versions:', 1)[1]
                versions = [ver.strip() for ver in versions_line.strip().split(",")]
        sorted_versions = sorted(versions, key=lambda v: Version(v))
        return sorted_versions
    except subprocess.CalledProcessError as e:
        logging.error(f"Error getting PyPI versions for {package_name}: {e.output}")
        return []

def find_lowest_valid_version(package_name, version_specifier):
    versions = get_available_versions(package_name)
    spec_set = SpecifierSet(version_specifier)

    for ver in versions:
        try:
            if Version(ver) in spec_set:
                logging.info(f"Lowest PyPI valid version for {package_name} matching '{version_specifier}': {ver}")
                return ver
        except InvalidVersion:
            continue
    logging.warning(f"No matching valid PyPI version found for {package_name} spec '{version_specifier}'")
    return None

def get_max_requirement_version(package_name):
    try:
        result = subprocess.check_output(["python3", "get_normal_max_versions.py", "max", package_name], text=True)
        result = result.strip()
        max_version_list = json.loads(result.replace("'", '"'))
        if max_version_list[0]:
            return max_version_list[0], max_version_list[1]
    except Exception as e:
        logging.error(f"Error getting max version from requirement file for {package_name}: {e}")
    return None, None

def main(package_name):
    logging.info(f"[dependency_resolver_final.py] Resolving explicitly dependencies for '{package_name}'")

    data = run_pipdeptree(package_name)
    package_info = get_package_info(data, package_name)

    if not package_info:
        logging.error(f"No such package info found for '{package_name}'")
        print("[]")
        sys.exit(1)

    dependency_issues = []
    dependencies = package_info.get("dependencies", [])

    for dep in dependencies:
        dep_name = dep.get("package_name")
        installed_version = dep.get("installed_version")
        required_specifier = dep.get("required_version", "").strip()

        if installed_version in ["?", None, ""]:
            logging.warning(f"Dependency '{dep_name}' has no installed version. Skipping.")
            continue

        if required_specifier.lower() in ["any", ""]:
            continue

        try:
            if Version(installed_version) not in SpecifierSet(required_specifier):
                py_version = find_lowest_valid_version(dep_name, required_specifier)
                req_version, req_file = get_max_requirement_version(dep_name)

                chosen_version = py_version

                if py_version and req_version:
                    if Version(req_version) > Version(py_version):
                        logging.info(
                            f"For '{dep_name}', requirement file version '{req_version}' found in '{req_file}' "
                            f"is higher than lowest PyPI valid '{py_version}'. Using higher '{req_version}' explicitly."
                        )
                        chosen_version = req_version
                    else:
                        logging.info(
                            f"For '{dep_name}', using PyPI lowest valid version '{py_version}' explicitly."
                        )
                elif req_version and not py_version:
                    logging.info(
                        f"For '{dep_name}', no valid PyPI version found; explicitly using "
                        f"requirement file version '{req_version}' from item '{req_file}'."
                    )
                    chosen_version = req_version
                elif not py_version and not req_version:
                    logging.warning(
                        f"No valid PyPI or requirement file version found explicitly for '{dep_name}'."
                    )
                    continue

                dep_specifier = f"{dep_name}=={chosen_version}"
                dependency_issues.append(dep_specifier)
                logging.info(
                    f"Dependency updated explicitly: '{dep_name}' installed '{installed_version}' "
                    f"doesn't satisfy '{required_specifier}'. Using explicitly '{chosen_version}'."
                )

        except Exception as ex:
            logging.error(f"Error explicitly processing dependency '{dep_name}': {ex}")

    logging.info(f"Explicit dependency issues resolved for '{package_name}': {dependency_issues}")
    print(json.dumps(dependency_issues))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logging.error("Incorrect usage clearly: python3 dependency_resolver_final.py <package_name> explicitly required.")
        print("[]")
        sys.exit(1)

    package_name = sys.argv[1].strip()
    try:
        main(package_name)
    except Exception as ex:
        logging.exception(f"Unexpected error explicitly processing '{package_name}': {ex}")
        print("[]")
        sys.exit(1)