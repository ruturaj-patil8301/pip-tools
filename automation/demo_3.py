import subprocess
import sys
import json
import logging
from packaging.version import Version, InvalidVersion

# Logging configuration
logging.basicConfig(
    filename='resolve_dependencies.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def run_command(cmd):
    try:
        output = subprocess.check_output(cmd, shell=True, text=True)
        logging.debug(f"Command succeeded '{cmd}': Output: {output.strip()}")
        return output.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed '{cmd}': {e.output}")
        return None

def get_installed_version(package_name):
    try:
        output = subprocess.check_output(["pip3", "show", package_name], text=True)
        for line in output.strip().splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()
        return None
    except subprocess.CalledProcessError:
        return None

def parse_dependency_issues(package):
    cmd = f'python3 dependency_resolver_final.py "{package}"'
    output = run_command(cmd)
    if output:
        try:
            issues_list = json.loads(output.strip().replace("'", '"'))
            return issues_list if isinstance(issues_list, list) else []
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing error parsing dependency issues for package {package}: {e}")
    return []

def parse_reverse_dependencies(package):
    cmd = f'python3 rev_dependency_resolver_final.py "{package}"'
    output = run_command(cmd)
    if output:
        try:
            rev_deps_list = json.loads(output.strip().replace("'", '"'))
            return rev_deps_list if isinstance(rev_deps_list, list) else []
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing error parsing reverse dependencies for package {package}: {e}")
    return []

def get_trail_version(package, current_version):
    cmd = f'python3 get_version_for_rev_dependendencies.py "{package}" "{current_version}" --trail'
    return run_command(cmd)

def install_package(package_spec):
    cmd = f'pip3 install "{package_spec}" --no-deps'
    if run_command(cmd) is not None:
        logging.info(f"Installed: {package_spec}")
        return True
    else:
        logging.error(f"Installation failed for: {package_spec}")
        return False

def main(package_list):
    upgrade_history = {}
    iteration = 0
    MAX_ITERATIONS = 10

    logging.info("=== Starting dependency resolution loop ===")

    while iteration < MAX_ITERATIONS:
        logging.info(f"--- Iteration {iteration + 1} ---")
        dependency_issue_packages = set()
        rev_deps_trail_packages = set()

        # Step 1: Resolve direct dependency issues
        for package in package_list:
            logging.info(f"Analyzing direct dependencies for {package}")
            issues = parse_dependency_issues(package)
            dependency_issue_packages.update(issues)

        # Step 2: Resolve reverse dependency issues
        for package in package_list:
            logging.info(f"Analyzing reverse dependencies for {package}")
            rev_deps = parse_reverse_dependencies(package)
            for rev_dep in rev_deps:
                current_version = get_installed_version(rev_dep)
                if not current_version:
                    logging.warning(f"Reverse dependency {rev_dep} not installed; skipping.")
                    continue
                trail_version = get_trail_version(rev_dep, current_version)
                if trail_version:
                    rev_deps_trail_packages.add(f"{rev_dep}=={trail_version}")
                else:
                    logging.warning(f"Could not determine trail version for {rev_dep}; skipping.")

        # Merge both sets of packages to install
        combined_install_list = set(dependency_issue_packages) | rev_deps_trail_packages
        if not combined_install_list:
            logging.info("No more packages to upgrade. Ending resolution loop.")
            break

        logging.info(f"Packages to upgrade in iteration {iteration + 1}: {combined_install_list}")

        # Step 3: Install packages explicitly without dependencies
        for pkg_spec in combined_install_list:
            if "==" in pkg_spec:
                pkg_name, pkg_version = pkg_spec.split("==")
            else:
                pkg_name = pkg_spec
                current_version = get_installed_version(pkg_name) or '0.0.0'
                pkg_version = get_trail_version(pkg_name, current_version)
                if not pkg_version:
                    logging.warning(f"Skipping {pkg_name}: cannot determine required version.")
                    continue
                pkg_spec = f"{pkg_name}=={pkg_version}"

            previous_version = get_installed_version(pkg_name) or "Not Installed"

            if install_package(pkg_spec):
                new_version = get_installed_version(pkg_name) or "Installation failed"
                upgrade_history[pkg_name] = {
                    "previous_version": previous_version,
                    "upgraded_version": new_version
                }

        iteration += 1

    # Final upgrade summary
    logging.info("=== Dependency resolution loop completed ===\n")
    print("\n--- Summary of Package Upgrades ---")
    for pkg, versions in upgrade_history.items():
        print(f"{pkg}: {versions['previous_version']} → {versions['upgraded_version']}")
        logging.info(f"{pkg}: {versions['previous_version']} → {versions['upgraded_version']}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"\nUsage: python3 {sys.argv[0]} '<package1>,<package2>,...'\n")
        sys.exit(1)

    packages_input = sys.argv[1]
    packages = [pkg.strip() for pkg in packages_input.strip().split(",") if pkg.strip()]

    if not packages:
        print("Error: No valid packages provided.")
        sys.exit(1)

    try:
        main(packages)
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}\nPlease check 'resolve_dependencies.log' for details.")
        sys.exit(1)
