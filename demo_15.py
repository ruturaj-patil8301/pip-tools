import subprocess
import sys
import json
from packaging.version import Version
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

def main(package_name):
    data = run_pipdeptree(package_name)
    package_info = get_package_info(data, package_name)

    if not package_info:
        print(f"Package '{package_name}' not found in pipdeptree output.")
        sys.exit(1)

    missing_packages = []
    dependency_issues = []

    dependencies = package_info.get("dependencies", [])
    for dep in dependencies:
        dep_name = dep.get("package_name")
        installed_version = dep.get("installed_version")
        required_version_spec = dep.get("required_version", "").strip()

        # Missing package case
        if installed_version == '?' or installed_version is None:
            missing_packages.append(dep_name)
            continue

        # No specific version constraints or explicitly "Any": always satisfied
        if required_version_spec.lower() == 'any' or required_version_spec == '':
            continue
        
        # Dependency issue case
        try:
            if Version(installed_version) not in SpecifierSet(required_version_spec):
                dependency_issues.append(f"{dep_name}{required_version_spec}")
        except Exception as e:
            print(f"Error checking version for {dep_name}: {e}")
            dependency_issues.append(f"{dep_name}{required_version_spec} (invalid specifier)")

    print("Missing packages:")
    print(missing_packages)

    print("\nDependency issue packages:")
    print(dependency_issues)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <package_name>")
        sys.exit(1)

    package_name = sys.argv[1]
    main(package_name)
