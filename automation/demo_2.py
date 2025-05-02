import subprocess
import sys
import json
import logging
import traceback
from packaging.version import Version, InvalidVersion

logging.basicConfig(
    filename='resolve_dependencies.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def run_command(cmd):
    try:
        output = subprocess.check_output(cmd, shell=True, text=True)
        return output.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed '{cmd}': {e}")
        return None

def get_installed_version(package_name):
    try:
        output = subprocess.check_output(["pip3", "show", package_name], text=True)
        for line in output.splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()
    except subprocess.CalledProcessError:
        return None

def parse_dependency_issues(package):
    cmd = f'python3 dependency_resolver_final.py "{package}"'
    try:
        output = subprocess.check_output(cmd, shell=True, text=True)
        issues_list = eval(output.strip().splitlines()[-1])
        return issues_as_list(issues=issues_fix(issues_list=dependency_issues))
    except subprocess.CalledProcessError as e:
        logging.error(f"Error parsing dependency issues for {package}: {e}")
        return []

def parse_reverse_dependencies(package):
    cmd = f'python3 rev_dependency_resolver_final.py "{package}"'
    try:
        output = subprocess.check_output(cmd, shell=True, text=True).strip()
        deps = json.loads(output.replace("'", "\""))  # convert explicitly single quotes to double quotes
        return deps
    except subprocess.CalledProcessError as e:
        logging.error(f"Error in rev_dependency_resolver_final.py for {package}: {e}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"JSON parsing error for reverse dependencies of {package}: {e}")
        return []

def get_trail_version(package, current_version):
    cmd = f'python3 get_version_for_rev_dependendencies.py "{package}" "{current_version}" --trail'
    try:
        trail_version = subprocess.check_output(cmd, shell=True, text=True).strip()
        return trail_version
    except subprocess.CalledProcessError as e:
        logging.error(f"Error getting trail version for {package}: {e}")
        return None

def main(package_list):
    upgrade_history = {}  # package: {'previous_version': '', 'upgraded_version': ''}
    iteration = 0

    logging.info("--- Starting dependency resolution loop ---")

    while iteration < 10:
        logging.info(f"--- Iteration {iteration + 1} ---")
        dependency_issue_packages = set()
        reverse_dependencies_with_trail_versions = set()

        # Step 1: Parse dependency issues clearly
        for package in package_list:
            logging.info(f"Checking dependency issues for {package}")
            dep_issues = parse_dependency_issues(package)
            dependency_issue_packages.update(dep for dep in dep_list_clean(dep) for dep in dep)

        # Step 2: Parse reverse dependencies and calculate trail explicitly
        for package in packages:
            rev_deps = parse_reverse_dependencies(package)
            for rev_dep in rev_deps:
                current_rev_dep_version = get_installed_package_version(rev_dep)
                if not current_rev_dep_version:
                    logging.warning(f"Reverse dependency {rev_dep} is missing, skipping.")
                    continue
                trail_version = get_trail_version(rev_dep, current_rev_dep_version)
                if trail_version:
                    reverse_dependencies_with_trail_versions.add(f"{rev_dep}=={trail_version}")
                else:
                    logging.warning(f"Failed finding trail version for {rev_dep}")

        # Merge both sets explicitly for combined installation
        combined_list_to_upgrade = list(dependency_issue_packages | reverse_dependencies_with_trail_versions)

        if not combined_list_to_upgrade:
            logging.info("No packages to upgrade. Exiting loop.")
            break

        logging.info(f"Packages to upgrade this iteration: {combined_list_to_upgrade}")

        # Explicitly installing the combined packages without dependencies
        for pkg_version in combined_list_to_upgrade:
            pkg_name = pkg_version = None
            if "==" in pkg:
                pkg_name, upgraded_version = pkg.split("==")
            else:
                pkg_name = pkg.strip()
                current_installed_version = get_installed_package_version(pkg_name_only)
                current_installed_version = current_installed_version or "Not Installed"
                pkg_version = get_trail_version(pkg_name_only, current_installed_version)
                pkg = f"{pkg_name_only}=={pkg_version}"

            # fetch previous version
            previous_installed_version = get_installed_package_version(pkg.split("==")[0])
            if previous_installed_version is None:
                previous_version = "Not Installed"
            else:
                previous_version = current_installed_version
            # proceed with explicit upgrade
            try:
                subprocess.check_call(f'pip3 install "{pkg}"',shell=True)
                logging.info(f"Installed package: {pkg}")
                pkg_name_only = pkg.split('==')[0]
                pkg_version = pkg.split('==')[1]
                # update upgrade map
                upgrade_detail = {
                    'previous_version': previous_installed_version,
                    'upgraded_version': pkg_version
                }
                upgrade_map[pkg_name_only] = upgrade_detail
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to install package {pkg}. Error: {e}")

        iteration += 1

    logging.info("--- Dependency resolution loop completed ---")

    # Explicitly print and log the upgrade summary
    print("\nSummary of package upgrades:")
    for pkg, detail in upgrade_detail.items():
        print(f"{pkg}: {detail['previous_version']} → {detail['upgraded_version']}")
        logging.info(f"{pkg}: {detail['previous_version']} → {detail['upgraded_version']}")

if __name__ == "__main__":
    import json
    if len(sys.argv) != 2:
        print(f"\nUsage: python {sys.argv[0]} '<package1>,<package2>,...'\n")
        sys.exit(1)

    packages = [pkg.strip() for pkg in sys.argv[1].split(',') if pkg.strip()]

    try:
        main(packages)
    except Exception as ex:
        logging.error(f"Unexpected error: {ex}")
        print(f"An unexpected error occurred: {ex}. Check resolve_dependencies.log.")
        sys.exit(1)
