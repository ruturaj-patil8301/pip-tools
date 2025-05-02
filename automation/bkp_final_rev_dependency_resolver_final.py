import subprocess
import sys
from packaging.requirements import Requirement
from packaging.version import Version
 
def get_installed_package_version(package_name):
    """Get installed version of the specified package."""
    try:
        output = subprocess.check_output(["pip3", "show", package_name], text=True)
        for line in output.strip().splitlines():
            if line.startswith("Version:"):
                return line.split(":")[1].strip()
        return None
    except subprocess.CalledProcessError:
        return None

def requirement_is_satisfied(requirement_str, current_version):
    """Check if version requirement is satisfied."""
    try:
        req = Requirement(requirement_str)
    except Exception as e:
        print(f"Warning: error parsing requirement '{requirement_str}': {e}")
        return None
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

    result = subprocess.check_output(cmd, shell=True, text=True)

    # A list to store packages whose requirements are NOT satisfied by current version
    problem_packages_detailed = []
    problem_packages_names_only = []

    for line in result.strip().split("\n"):
        if not line:
            continue
        dependent_package, required_spec = line.split(";", 1)

        if required_spec.strip() == package_name:
            continue

        requirement_str = f"{package_name}{required_spec}"

        satisfied = requirement_is_satisfied(requirement_str, current_version)

        # Skip explicitly if parsing error (None)
        if satisfied is None:
            continue

        # Append explicitly only if requirement truly unsatisfied (False)
        if not satisfied:
            problem_packages_detailed.append(line)
            # Extract package name only without the version info.
            pkg_name_only = dependent_package.split("==")[0].strip()
            problem_packages_names_only.append(pkg_name_only)

    # print the problematic packages clearly
    # print("Packages with unsatisfied dependency requirements:")
    # if problem_packages_detailed:
    #     for pkg in problem_packages_detailed:
    #         print(pkg)
    # else:
    #     print("None (All dependencies satisfied!)")

    #print("\nProblematic package names only (list):")
    print(problem_packages_names_only)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <package_name>")
        sys.exit(1)
    package_name = sys.argv[1]
    main(package_name)
