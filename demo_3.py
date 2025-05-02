import re
import subprocess
from packaging import version

def get_package_dependency_tree(package_name):
    try:
        result = subprocess.run(
            ["pipdeptree", "-p", package_name],
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

def compare_versions(required, installed):
    if installed == '?':
        return 'unknown'
    
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
    package_name = input("Enter the package name: ")
    package_data = get_package_dependency_tree(package_name)
    
    if package_data:
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
