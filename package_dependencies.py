import subprocess
import json
import argparse

def get_dependency_tree_json(package_name):
    """Get the dependency tree for a package as JSON using pipdeptree."""
    try:
        result = subprocess.run(['pipdeptree', '-p', package_name, '--json'], 
                              capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running pipdeptree: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(result.stdout)
        return None

def get_reverse_dependencies(package_name):
    """Call the reverse dependency script and analyze its output."""
    try:
        result = subprocess.run(['python3', 'get_rev_dependencies.py', package_name], 
                                capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running reverse dependency script: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(result.stdout)
        return None

def main():
    parser = argparse.ArgumentParser(description="Print dependencies and reverse dependencies of a package.")
    parser.add_argument('package_name', type=str, help='The name of the package to analyze.')
    args = parser.parse_args()
    
    package_name = args.package_name
    
    # Get the dependency tree in JSON format
    dependency_tree = get_dependency_tree_json(package_name)
    if dependency_tree is None:
        print(f"Failed to retrieve dependency tree for {package_name}")
        return

    # Get reverse dependencies
    reverse_dependencies = get_reverse_dependencies(package_name)
    if reverse_dependencies is None:
        print(f"Failed to retrieve reverse dependencies for {package_name}")
        return

    # Print results
    print("Dependencies:")
    print(json.dumps(dependency_tree, indent=4))

    print("\nReverse Dependencies:")
    print(json.dumps(reverse_dependencies, indent=4))

if __name__ == "__main__":
    main()