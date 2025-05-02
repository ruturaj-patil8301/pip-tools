import subprocess
import json
import re
import argparse

def get_reverse_dependencies(package_name):
    # Run the pipdeptree command with grep to filter the output
    command = f"pipdeptree --reverse --packages {package_name} 2>/dev/null | grep -i {package_name}"
    
    try:
        # Execute the command
        output = subprocess.check_output(command, shell=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return None

    # Print the raw output for debugging
    #print("Raw output from pipdeptree:")
    #print(output)

    dependencies = []
    lines = output.strip().split('\n')
    
    if not lines:
        return {
            "package": package_name,
            "version": "unknown",
            "dependencies": []
        }

    # The first line contains the main package and its version
    main_package_info = lines[0].strip().split('==')
    main_package = main_package_info[0]
    main_version = main_package_info[1]

    # Iterate through the dependency lines
    for line in lines[1:]:
        # Match each line to capture package name, version, and requirements
        # This regex accounts for leading whitespace and the arrow character
        match = re.match(r'^\s*├──\s*(\S+)==(\S+)\s+\[requires:\s*(.+?)\]', line.strip()) or \
                re.match(r'^\s*└──\s*(\S+)==(\S+)\s+\[requires:\s*(.+?)\]', line.strip())
        
        if match:
            dep_package = match.group(1)
            dep_version = match.group(2)
            requires = match.group(3)
            dependencies.append({
                "package": dep_package,
                "version": dep_version,
                "requires": requires
            })
    
    # Create the final JSON structure
    result = {
        "package": main_package,
        "version": main_version,
        "dependencies": dependencies
    }
    
    return result

if __name__ == "__main__":
    # Set up argument parsing to get the package name from command line
    parser = argparse.ArgumentParser(description="Get reverse dependencies of a package.")
    parser.add_argument('package_name', type=str, help='The name of the package to analyze.')
    args = parser.parse_args()
    
    # Get the JSON output
    json_output = get_reverse_dependencies(args.package_name)
    
    if json_output:
        # Print the JSON result to standard output
        print(json.dumps(json_output, indent=4))