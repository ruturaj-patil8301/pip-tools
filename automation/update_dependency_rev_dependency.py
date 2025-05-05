import subprocess
import sys
import logging
import ast
import json
from packaging.version import Version, InvalidVersion

# Configure logging to write to a file with timestamp, level, and message
logging.basicConfig(
    filename='resolve_dependencies.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def run_command(cmd):
    """
    Execute a shell command and capture its output.
    
    Args:
        cmd (str): Shell command to execute
        
    Returns:
        str or None: Command output if successful, None if command fails
        
    Logs:
        - DEBUG: Command output on success
        - ERROR: Command error on failure
    """
    try:
        output = subprocess.check_output(cmd, shell=True, text=True)
        logging.debug(f"Command succeeded '{cmd}': Output: {output.strip()}")
        return output.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed '{cmd}': {e.output}")
        return None

def get_installed_version(package_name):
    """
    Get the installed version of a Python package.
    
    Args:
        package_name (str): Name of the package to check
        
    Returns:
        str or None: Version string if package is installed, None otherwise
        
    Note:
        Uses pip3 show to get package information
    """
    try:
        output = subprocess.check_output(["pip3", "show", package_name], text=True)
        for line in output.strip().splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()
    except subprocess.CalledProcessError:
        return None

def parse_dependency_issues(package):
    """
    Parse dependency issues for a package using dependency_resolver_final.py.
    
    Args:
        package (str): Name of the package to analyze
        
    Returns:
        list: List of dependency issues found
        
    Logs:
        - ERROR: If parsing fails
        
    Note:
        Expects dependency_resolver_final.py to output a list in string format
    """
    cmd = f'python3 dependency_resolver_final.py "{package}"'
    output = run_command(cmd)
    if output:
        try:
            issues_list = ast.literal_eval(output.strip())
            if isinstance(issues_list, list):
                return issues_list
        except (ValueError, SyntaxError) as e:
            logging.error(f"Error parsing dependency issues for {package}: {e}")
    return []

def parse_reverse_dependencies(package):
    """
    Parse reverse dependencies for a package using rev_dependency_resolver_final.py.
    
    Args:
        package (str): Name of the package to analyze
        
    Returns:
        list: List of reverse dependencies found
        
    Logs:
        - ERROR: If parsing fails
        
    Note:
        Expects rev_dependency_resolver_final.py to output a list in string format
    """
    cmd = f'python3 rev_dependency_resolver_final.py "{package}"'
    output = run_command(cmd)
    if output:
        try:
            rev_deps_list = ast.literal_eval(output.strip())
            if isinstance(rev_deps_list, list):
                return rev_deps_list
        except (ValueError, SyntaxError) as e:
            logging.error(f"Error parsing reverse dependencies for {package}: {e}")
    return []

def get_trail_version(package, current_version):
    """
    Get a trail version for a package using get_version_for_rev_dependendencies.py.
    
    A trail version is a version between the current version and the latest version,
    used to gradually upgrade packages with complex dependency relationships.
    
    Args:
        package (str): Name of the package
        current_version (str): Current version of the package
        
    Returns:
        str or None: Trail version if found, None otherwise
        
    Note:
        Uses get_version_for_rev_dependendencies.py with --trail flag
    """
    cmd = f'python3 get_version_for_rev_dependendencies.py "{package}" "{current_version}" --trail'
    return run_command(cmd)

def install_package(package_spec):
    """
    Install a Python package with a specific version.
    
    Args:
        package_spec (str): Package specification (e.g., "package==1.0.0")
        
    Returns:
        bool: True if installation succeeded, False otherwise
        
    Logs:
        - INFO: Installation success
        - ERROR: Installation failure
        
    Note:
        Uses pip3 install with --no-deps to avoid dependency conflicts
    """
    cmd = f'pip3 install "{package_spec}" --no-deps'
    if run_command(cmd) is not None:
        logging.info(f"Installed: {package_spec}")
        return True
    else:
        logging.error(f"Installation failed for: {package_spec}")
        return False

def main(initial_packages):
    """
    Main function to resolve and update package dependencies.
    
    This function:
    1. Iteratively resolves direct dependency issues
    2. Resolves reverse dependency issues
    3. Upgrades packages to resolve these issues
    4. Tracks upgrade history
    
    Args:
        initial_packages (list): List of package names to start with
        
    Returns:
        dict: Upgrade history mapping package names to version changes
        
    Logs:
        - INFO: Start and end of resolution process
        - INFO: Iteration progress
        - INFO: Package analysis and upgrades
        - WARNING: Missing packages or versions
    """
    upgrade_history = {}
    iteration = 0
    MAX_ITERATIONS = 10

    logging.info("=== Starting dependency resolution loop ===")

    packages_to_check = set(initial_packages)

    while iteration < MAX_ITERATIONS and packages_to_check:
        iteration += 1
        logging.info(f"--- Iteration {iteration} ---")
        dependency_issue_packages = set()
        rev_deps_trail_packages = set()

        # Step 1: Resolve direct dependency issues explicitly only for the relevant packages
        for package in packages_to_check:
            logging.info(f"Analyzing direct dependencies for package: {package}")
            dep_issues = parse_dependency_issues(package)
            dependency_issue_packages.update(dep_issues)

        # Step 2: Resolve reverse dependency explicitly only for the relevant packages
        for package in packages_to_check:
            logging.info(f"Analyzing reverse dependencies for package: {package}")
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
                    logging.warning(f"No trail version found for {rev_dep}")

        # Combine both dependency types for installation
        combined_list_to_upgrade = dependency_issue_packages | rev_deps_trail_packages
        logging.info(f"Packages to upgrade in iteration {iteration}: {combined_list_to_upgrade}")

        if not combined_list_to_upgrade:
            logging.info("No more packages to upgrade. Ending resolution loop.")
            break

        # Next iteration—we'll explicitly only check packages we changed/upgraded during this iteration
        packages_to_check_next_iteration = set()

        for pkg_spec in combined_list_to_upgrade:
            if "==" in pkg_spec:
                pkg_name, pkg_version = pkg_spec.split("==")
            else:
                pkg_name = pkg_spec.strip()
                current_version = get_installed_version(pkg_name) or '0.0.0'
                pkg_version = get_trail_version(pkg_name, current_version)
                if not pkg_version:
                    logging.warning(f"Skipping {pkg_name}: cannot determine required version.")
                    continue
                pkg_spec = f"{pkg_name}=={pkg_version}"

            previous_version = get_installed_version(pkg_name) or "Not Installed"

            if install_package(pkg_spec):
                new_version = get_installed_version(pkg_name) or "Installation failed"
                logging.info(f"{pkg_name}: {previous_version} → {new_version}")

                # Record in upgrade history
                upgrade_history[pkg_name] = {
                    "previous_version": previous_version,
                    "upgraded_version": new_version
                }

                # Explicitly add this upgraded package to check in the next iteration.
                if previous_version != new_version:
                    packages_to_check_next_iteration.add(pkg_name)
            else:
                logging.error(f"Installation failed explicitly for package: {pkg_spec}")

        # For next iteration, scrutinize explicitly only packages upgraded in this iteration
        packages_to_check = packages_to_check_next_iteration

    # Explicit upgrade summary print and log
    logging.info("=== Dependency resolution loop completed ===\n")
    print("\n--- Summary of Package Upgrades ---")
    for pkg, versions in upgrade_history.items():
        print(f"{pkg}: {versions['previous_version']} → {versions['upgraded_version']}")
        logging.info(f"{pkg}: {versions['previous_version']} → {versions['upgraded_version']}")
    
    return upgrade_history

if __name__ == "__main__":
    """
    Command-line interface for dependency resolution.
    
    Usage:
        python update_dependency_rev_dependency.py '<package1>,<package2>,...'
    
    Args:
        A comma-separated list of package names
    
    Outputs:
        - Prints a summary of package upgrades
        - Writes upgrade history to upgrade_history.json
    
    Exits:
        - With code 1 if no valid packages are provided
        - With code 1 if an unexpected error occurs
    
    Logs:
        - ERROR: If arguments are invalid
        - ERROR: If an unexpected error occurs
    """
    if len(sys.argv) != 2:
        print(f"\nUsage: python3 {sys.argv[0]} '<package1>,<package2>,...'\n")
        sys.exit(1)

    packages_input = sys.argv[1]
    packages = [pkg.strip() for pkg in packages_input.strip().split(",") if pkg.strip()]

    if not packages:
        print("Error: No valid packages provided.")
        sys.exit(1)

    try:
        result = main(packages)
        # Write the upgrade history to a temporary file for wrapper.py to read
        with open('upgrade_history.json', 'w') as f:
            json.dump(result, f)
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}\nPlease check 'resolve_dependencies.log' for details.")
        sys.exit(1)
