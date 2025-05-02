import subprocess
import sys
import json
import logging
from packaging.version import Version
from packaging.requirements import Requirement

# Configure logging to append clearly to the same unified log file
logging.basicConfig(
    filename='resolve_dependencies.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_installed_package_version(package_name):
    """Get installed version of the specified package explicitly."""
    try:
        output = subprocess.check_output(["pip3", "show", package_name], text=True)
        for line in output.strip().splitlines():
            if line.startswith("Version:"):
                return line.split(":")[1].strip()
        return None
    except subprocess.CalledProcessError:
        logging.error(f"pip3 show failed for package: {package_name}")
        return None

def requirement_is_satisfied(requirement_str, current_version):
    """Check clearly if version requirement is satisfied explicitly."""
    try:
        req = Requirement(requirement_str)
        installed_version = Version(current_version)
        return installed_version in req.specifier
    except Exception as e:
        logging.error(f"Error parsing requirement '{requirement_str}' with installed version '{current_version}': {e}")
        return None

def main(package_name):
    current_version = get_installed_package_version(package_name)
    if current_version is None:
        logging.error(f"Package '{package_name}' not found explicitly installed via pip.")
        print("[]")  # explicitly empty output list to avoid parsing error
        sys.exit(1)

    cmd = (
        f'pipdeptree -p "{package_name}" --reverse 2>/dev/null'
        f'| grep -iE "\\[requires: {package_name}" '
        f'| awk \'{{print $2";"$4}}\' | tr -d \'[]\' | sort -u'
    )
    try:
        result = subprocess.check_output(cmd, shell=True, text=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running pipdeptree command: {e.output}")
        print("[]")
        sys.exit(1)

    problem_packages_names_only = []

    for line in result.strip().split("\n"):
        if not line:
            continue
        dependent_package, required_spec = line.split(";", 1)

        # No specifier explicitly required, so always satisfied explicitly.
        if required_spec.strip() == package_name:
            continue

        requirement_str = f"{package_name}{required_spec}"

        satisfied = requirement_is_satisfied(requirement_str, current_version)

        if satisfied is None:
            logging.warning(f"Could not parse requirement '{requirement_str}' for '{dependent_package}'. Skipping explicitly.")
            continue

        if not satisfied:
            pkg_name_only = dependent_package.split("==")[0].strip()
            logging.info(f"Reverse dependency issue identified: {dependent_package} requires '{requirement_str}' but {current_version} is installed.")
            problem_packages_names_only.append(pkg_name_only)

    # Log the problematic reverse dependency packages explicitly.
    logging.info(f"Reverse dependency issues identified for '{package_name}': {problem_packages_names_only}")

    # Always explicitly output a well-formed JSON to stdout explicitly to be easily parsed by calling scripts
    print(json.dumps(problem_packages_names_only))

# Explicitly ensure required functions exist:
def get_installed_package_version(package_name):
    try:
        output = subprocess.check_output(["pip3", "show", package_name], text=True)
        for line in output.strip().splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"pip3 show command failed for {package_name}: {e}")
        return None

def requirement_is_satisfied(requirement_str, current_version):
    try:
        req = Requirement(requirement_str)
        installed_version = Version(current_version)
        return installed_version in req.specifier
    except Exception as e:
        logging.error(f"Error parsing requirement: {requirement_str}, version: {current_version}: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logging.error(f"Invalid invocation! Correct usage: python3 {sys.argv[0]} <package_name>")
        print("[]")
        sys.exit(1)
    package_name = sys.argv[1]
    problem_packages_names_only = []
    main(package_name)
    #print(f"Problematic packages for '{package_name}': {problem_packages_names_only}") # Outputs explicitly
    #print(json.dumps(problem_packages_names_only)) # Outputs JSON explicitly
