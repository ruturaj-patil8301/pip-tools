import subprocess
import sys
from packaging.requirements import Requirement
from packaging.version import Version

def get_installed_package_version(package_name):
    """Get installed version of the specified package."""
    try:
        output = subprocess.check_output(["pip", "show", package_name], text=True)
        for line in output.strip().split("\n"):
            if line.startswith("Version:"):
                return line.split()[1].strip()
    except subprocess.CalledProcessError:
        return None

def requirement_is_satisfied(requirement_str, current_version):
    """
    Check if installed version satisfies a given requirement specifier.

    requirement_str: e.g. 'cryptography>=3.3,<46.0.0'
    current_version: e.g. '42.0.8'
    """
    try:
        req = Requirement(requirement_str)
    except Exception as e:
        print(f"Unable to parse requirement: {requirement_str}. Error: {e}")
        return False

    installed_version = Version(current_version)
    
    # If there's no version specifier at all, the requirement is always satisfied
    if not req.specifier:
        return True

    # Check if the installed version meets the requirement specifier
    return installed_version in req.specifier

def main(package_name):
    # Get the current installed version of the package
    current_version = get_installed_package_version(package_name)
    if current_version is None:
        print(f"Error: Package '{package_name}' not found.")
        sys.exit(1)

    print(f"Package '{package_name}' is installed with version: {current_version}\n")

    # Run pipdeptree command to get dependencies
    cmd = (
        f'pipdeptree -p "{package_name}" --reverse 2>/dev/null | '
        f'grep -iE "\\[requires: {package_name}" | '
        f'awk \'{{print $2";"$4}}\' | tr -d \'[]\' | sort -u'
    )
    result = subprocess.check_output(cmd, shell=True, text=True)

    # List to store problematic dependencies
    problem_packages = []

    print(f"Checking dependencies for {package_name} (current version {current_version}):")
    for line in result.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        dependent_package, required_spec = line.split(";", 1)

        # Build proper requirement string
        if required_spec.strip() == package_name:
            # no version specifier, just package name
            requirement_str = package_name
        else:
            # e.g.: 'cryptography>=3.3,<46.0.0'
            requirement_str = f"{package_name}{required_spec.replace(' ','')}"

        # Check if requirement is satisfied
        if not requirement_is_satisfied(requirement_str, current_version):
            # not satisfied (negative case), add to list
            print(f"[FAIL] Dependency unsatisfied for {dependent_package}: {requirement_str}, current version: {current_version}")
        else:
            print(f"[OK] {dependent_package} requirement '{requirement_str}' meets installed version ({current_version})")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <package_name>")
        sys.exit(1)
    package_name = sys.argv[1]
    main(package_name)
