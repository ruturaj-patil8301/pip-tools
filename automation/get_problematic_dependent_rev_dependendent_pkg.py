import re
import subprocess
import argparse
from packaging import specifiers, version

def get_package_dependency_tree(package_name, reverse=False):
    command = ["pipdeptree", "-p", package_name]
    if reverse:
        command.append("--reverse")
    
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
            text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running pipdeptree: {e}")
        return None

def parse_package_data(data):
    packages = []
    lines = data.strip().split('\n')
    
    for line in lines:
        match = re.match(r'^[├└│─]*\s*(\S+)\s\[required:\s*([^,]+),\s*installed:\s*(\S+)\]', line)
        if match:
            name = match.group(1)
            required_version = match.group(2).strip()
            installed_version = match.group(3).strip()
            packages.append((name, required_version, installed_version))
    
    return packages

def parse_reverse_package_data(data):
    packages = []
    installed_version = None
    lines = data.strip().split('\n')
    
    for line in lines:
        # Extract the main package version
        match = re.match(r'^(\S+)==([\d\.]+)', line)
        if match:
            installed_version = match.group(2)
            continue
        
        # Extract the reverse dependency lines
        match = re.match(r'^[├└│─]*\s*(\S+)==([\d\.]+)\s\[requires:\s*(.*)\]', line)
        if match:
            name = match.group(1)  # Get package name only for reverse case
            current_version = match.group(2)
            required_version = match.group(3).strip()
            packages.append((name, current_version, required_version))
    
    return installed_version, packages

def validate_reverse_dependencies(installed_version, packages, main_package_name):
    problems_found = False
    problematic_packages = []

    for name, current_version, required_version in packages:
        # Strip the main package name from the start of the required_version
        if required_version.startswith(main_package_name):
            required_version = required_version[len(main_package_name):].strip()
        
        if not required_version:
            print(f"{name}: requires {main_package_name} [OK]")
            continue
        
        try:
            specifier_set = specifiers.SpecifierSet(required_version)
            if not version.parse(installed_version) in specifier_set:
                print(f"{name}: requires {main_package_name} {required_version} [NOT OK]")
                problems_found = True
                problematic_packages.append((name, current_version))
            else:
                print(f"{name}: requires {main_package_name} {required_version} [OK]")
        except specifiers.InvalidSpecifier as e:
            print(f"Warning: Invalid specifier '{required_version}' for package '{name}'. Skipping check.")
            continue
    
    return problems_found, problematic_packages

def compare_versions(required, installed):
    if installed == '?':
        return 'unknown'
    
    if required.lower() == 'any':
        return 'ok'
    
    # Extract version number from required version constraint
    required_version = re.match(r'^[^\d]*([\d\.]+)', required).group(1)
    
    if version.parse(installed) < version.parse(required_version):
        return 'problematic'
    return 'ok'

def highlight_packages(packages):
    problematic_packages = {}
    
    for name, required_version, installed_version in packages:
        status = compare_versions(required_version, installed_version)
        if status == 'problematic':
            print(f'{name}: required {required_version}, installed {installed_version} [PROBLEMATIC]')
            problematic_packages[name] = required_version
        elif status == 'unknown':
            print(f'{name}: required {required_version}, installed {installed_version} [UNKNOWN]')
        else:
            print(f'{name}: required {required_version}, installed {installed_version} [OK]')
    
    return problematic_packages

def main():
    parser = argparse.ArgumentParser(description="Check for problematic package versions in dependencies.")
    parser.add_argument("package_name", help="Name of the package to check.")
    parser.add_argument("--reverse", action="store_true", help="Check reverse dependencies.")
    args = parser.parse_args()
    
    package_data = get_package_dependency_tree(args.package_name, reverse=args.reverse)
    
    if package_data:
        if args.reverse:
            installed_version, package_list = parse_reverse_package_data(package_data)
            problems_found, problematic_packages = validate_reverse_dependencies(installed_version, package_list, args.package_name)
            print("\nAll checks complete.")
            if problems_found:
                print("There are problematic packages in the reverse dependencies:")
                for pkg_name, curr_version in problematic_packages:
                    print(f"{pkg_name}: {curr_version}")
            else:
                print("No problematic packages found in the reverse dependencies.")
        else:
            package_list = parse_package_data(package_data)
            problematic_packages = highlight_packages(package_list)
            if problematic_packages:
                print("\nProblematic packages and their required versions:")
                for pkg_name, req_version in problematic_packages.items():
                    print(f"{pkg_name}: {req_version}")
            else:
                print("No problematic packages found.")
    else:
        print("Failed to retrieve package dependency tree.")

if __name__ == "__main__":
    main()
