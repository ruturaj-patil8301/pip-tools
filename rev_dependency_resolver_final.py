import subprocess
import sys
from packaging.requirements import Requirement
from packaging.version import Version

def get_installed_package_version(package_name):
    """Get installed version of the specified package."""
    try:
        output = subprocess.check_output(["pip", "show", package_name], text=True)
        for line in output.strip().splitlines():
            if line.startswith("Version:"):
                return line.split(":")[1].strip()
        return None
    except subprocess.CalledProcessError:
        return None

def requirement_is_satisfied(requirement_str, current_version):
    """
    Check if version requirement is satisfied.

    requirement_str: e.g. 'cryptography>=3.3,<46.0.0'
    current_version: e.g. '42.0.8'
    """
    #print(f"Checking requirement: {requirement_str} against installed version: {current_version}")
    try:
        req = Requirement(requirement_str)
    except Exception as e:
        print(f"Warning: error parsing requirement '{requirement_str}': {e}")
        return False
    installed_version = Version(current_version)
    return installed_version in req.specifier

def main(package_name):
    current_version = get_installed_package_version(package_name)
    if current_version is None:
        print(f"Error: Package '{package_name}' not found.")
        sys.exit(1)

    cmd = (
        f'pipdeptree -p "{package_name}" --reverse 2>/dev/null '
        f'| grep -iE "\\[requires: {package_name}" '
        f'| awk \'{{print $2";"$4}}\' | tr -d \'[]\' | sort -u'
    )

    #result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    result = subprocess.check_output(cmd, shell=True, text=True)
    #print(f"Result of pipdeptree command:\n{result}")

    # A list to store packages whose requirements are NOT satisfied by current version
    problem_packages = []

    for line in result.strip().split("\n"):
        #print(f"Processing line: {line}")
        if not line:
            continue
        dependent_package, required_spec = line.split(";", 1)
        #print(f"Dependent package: {dependent_package} Required spec: {required_spec}")

        # Handle the case when required_spec is empty (just package name)
        if required_spec.strip() == package_name:
            # No specific version explicitly required, so requirement always satisfied
            #print(f"Package '{dependent_package}' does not require a specific version of '{package_name}'.")
            continue

        requirement_str = f"{package_name}{required_spec}"
        #print(f"package_name: {package_name} required_spec: {required_spec}")
        #print(f"Checking requirement: {requirement_str} against installed version: {current_version}")
        if not requirement_is_satisfied(required_spec, current_version):
            problem_packages.append(line)

    # print the problematic packages clearly
    print("Packages with unsatisfied dependency requirements:")
    if problem_packages:
        for pkg in problem_packages:
            print(pkg)
    else:
        print("None (All dependencies satisfied!)")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <package_name>")
        sys.exit(1)

    package_name = sys.argv[1]
    main(package_name)
