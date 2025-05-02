import subprocess
import json
import re
import argparse
import pkg_resources
from pkg_resources import parse_version

def parse_requirements(req_string):
    """Parse version requirements more accurately."""
    if not req_string or req_string == 'Any':
        return []
    
    # Handle complex requirement strings
    if ',' in req_string:
        parts = req_string.split(',')
    else:
        parts = [req_string]
    
    specs = []
    for part in parts:
        specs.extend(pkg_resources.Requirement.parse(f"requirement{part.strip()}").specs)
    return specs

def is_version_compatible(version, requirement_specs):
    """
    Check if version is compatible with requirement specs.
    Returns (bool, str) tuple of (is_compatible, reason)
    """
    #print(f"Checking compatibility for version: {version}")
    #print(f"Requirement specs: {requirement_specs}")
    if not requirement_specs:
        return True, ""
    
    version = parse_version(version)
    
    for op, req_version in requirement_specs:
        req_version = parse_version(req_version)
        #print  (f"Checking {version} {op} {req_version}")
        
        if op == '==':
            if version != req_version:
                return False, f"requires exactly {req_version}"
        elif op == '>=':
            if version < req_version:
                return False, f"requires >= {req_version}"
        elif op == '<=':
            if version > req_version:
                return False, f"requires <= {req_version}"
        elif op == '>':
            if version <= req_version:
                return False, f"requires > {req_version}"
        elif op == '<':
            if version >= req_version:
                return False, f"requires < {req_version}"
        elif op == '!=':
            if version == req_version:
                return False, f"requires != {req_version}"
        elif op == '~>':
            major_req_version = f"{req_version.major}.*"
            if version.major != req_version.major or (version.minor and version.minor != req_version.minor):
                return False, f"requires ~> {req_version.major}.{req_version.minor}"
        elif op == '^':
            if version.major != req_version.major or version.minor < req_version.minor:
                return False, f"requires ^{req_version}"
        elif op == '||':
            valid_versions = [parse_version(v) for v in req_version.split('||')]
            if version not in valid_versions:
                return False, f"requires one of {valid_versions}"
        elif op == 'Range':
            lower_bound, upper_bound = req_version.split(',')
            lower_op, lower_version = lower_bound.split(' ')
            upper_op, upper_version = upper_bound.split(' ')
            lower_version = parse_version(lower_version)
            upper_version = parse_version(upper_version)
            return (is_version_compatible(version, [(lower_op, lower_version)])[0] and
                    is_version_compatible(version, [(upper_op, upper_version)])[0]), \
                   f"requires range {req_version}"
        elif '*' in str(req_version):
            pattern = re.sub(r'\*', r'\\d+', str(req_version))
            if not re.match(pattern, str(version)):
                return False, f"requires {req_version}"
            
    return True, ""

def get_dependency_tree_json(package_name):
    """Get the dependency tree for a package as JSON using pipdeptree."""
    try:
        result = subprocess.run(['pipdeptree', '-p', package_name, '--json'], 
                              capture_output=True, text=True, check=True)
        #print(f"Raw output from pipdeptree: {result.stdout}")
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running pipdeptree: {e}")
        return None

def find_problematic_dependencies(dependency_tree):
    """Identify discrepancies in dependency versions."""
    problematic_dependencies = []
    
    for package in dependency_tree:
        print(f"Package Object: {package}")
        installed_version = package['package']['installed_version']
        dependencies = package.get('dependencies', [])
        #print(f"Checking package: {package['package']['package_name']} (installed version: {installed_version})")
        
        for dep in dependencies:
            required_version = dep.get('required_version', 'Any')
            #print(f"  - Package: {package['package']['package_name']} Dependency: {dep['package_name']} (required version: {required_version})")
            
            if required_version != 'Any':
                requirement_specs = parse_requirements(required_version)
                #print(f"    - Requirement specs: {requirement_specs}")
                is_compatible, reason = is_version_compatible(installed_version, requirement_specs)
                #print(f"    - Compatibility check: {is_compatible} ({reason})")
                
                if not is_compatible:
                    problematic_dependencies.append({
                        "package": dep['package_name'],
                        "installed_version": dep.get('installed_version', 'Unknown'),
                        "required_version": required_version
                    })
    
    return problematic_dependencies

def check_reverse_dependencies(package_name):
    """Call the reverse dependency script and analyze its output for discrepancies."""
    try:
        result = subprocess.run(['python3', 'get_rev_dependencies.py', package_name], 
                                capture_output=True, text=True, check=True)
        reverse_dependencies = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running reverse dependency script: {e}")
        return []

    problematic_reverse_dependencies = []
    for dep in reverse_dependencies['dependencies']:
        required_version = dep.get('requires', 'Any')
        dep_package_name = dep.get('package', 'Unknown')
        dep_installed_version = dep.get('version', 'Unknown')
        if required_version != 'Any':
            requirement_specs = parse_requirements(required_version)
            #print(f"Checking reverse dependency: {dep_package_name} (installed version: {dep_installed_version})")
            #print(f" Reverse Dependency Version: {reverse_dependencies['version']}")
            is_compatible, reason = is_version_compatible(reverse_dependencies['version'], requirement_specs)
            
            if not is_compatible:
                problematic_reverse_dependencies.append({
                    "package": dep_package_name,
                    "installed_version": dep_installed_version,
                    "required_version": required_version
                })
    
    return problematic_reverse_dependencies

def main():
    parser = argparse.ArgumentParser(description="Check dependency tree for a package.")
    parser.add_argument('package_name', type=str, help='The name of the package to analyze.')
    args = parser.parse_args()
    
    package_name = args.package_name
    
    # Get the dependency tree in JSON format
    dependency_tree = get_dependency_tree_json(package_name)
    if not dependency_tree:
        return

    # Find and print problematic dependencies
    print(f"Checking dependencies for {package_name}")
    problematic_dependencies = find_problematic_dependencies(dependency_tree)
    
    if problematic_dependencies:
        print("\nProblematic dependencies:")
        for dep in problematic_dependencies:
            print(json.dumps(dep, indent=4))
    else:
        print("All dependencies are compatible.")

    #Check reverse dependencies
    #print(f"\nChecking reverse dependencies for {package_name}")
    problematic_reverse_dependencies = check_reverse_dependencies(package_name)
    
    if problematic_reverse_dependencies:
        print("\nProblematic reverse dependencies:")
        for dep in problematic_reverse_dependencies:
            print(json.dumps(dep, indent=4))
    else:
        print("All reverse dependencies are compatible.")

if __name__ == "__main__":
    main()