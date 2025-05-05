import os
import sys
import subprocess
import logging
import json
import yaml
from packaging.version import Version

# Configure logging 
logging.basicConfig(
    filename='resolve_dependencies.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Check if packages explicitly provided from command line
if len(sys.argv) < 2 or not sys.argv[1].strip():
    error_msg = "Error: No package arguments provided. Please pass packages like 'cryptography==42.0.8 Flask==3.0.2'."
    logging.error(error_msg)
    print(error_msg)
    sys.exit(1)

# Parse packages explicitly from command line
input_packages = []
skip_max_version_check = False

# Check for flags in arguments
for arg in sys.argv[1:]:
    if arg == "--skip-max-version-check":
        skip_max_version_check = True
        logging.info("Max version check will be skipped due to --skip-max-version-check flag")
        print("Flag detected: Skipping max version check")
    elif arg.startswith("--"):
        logging.warning(f"Unknown flag: {arg}")
    else:
        # Split the argument by spaces to support multiple packages in a single argument
        packages_in_arg = arg.split()
        for pkg in packages_in_arg:
            if '==' in pkg:  # Only add if it's a valid package spec
                input_packages.append(pkg)
            else:
                logging.warning(f"Ignoring invalid package specification: {pkg}")

if not input_packages:
    error_msg = "Error: No valid package specifications found. Expected format: package==version."
    logging.error(error_msg)
    print(error_msg)
    sys.exit(1)

package_specs = ' '.join(input_packages)
packages_to_update = [pkg.split('==')[0] for pkg in input_packages if '==' in pkg]
upgraded_versions = [pkg.split('==')[1] for pkg in input_packages if '==' in pkg]
print(f"Packages to update: {packages_to_update}")
print(f"Package specs: {package_specs}")
print(f"Upgraded versions: {upgraded_versions}")

if not packages_to_update:
    error_msg = "Error: Argument format incorrect. Expected format: package==version."
    logging.error(error_msg)
    print(error_msg)
    sys.exit(1)

logging.info(f"Packages provided: {package_specs}")
print(f"Packages provided for installation: {package_specs}")

# --- Get max versions ---
if not skip_max_version_check:
    for idx, pkg in enumerate(packages_to_update):
        provided_version = input_packages[idx].split('==')[1]
        try:
            # Run command to explicitly get max available version
            result = subprocess.run(
                ['python3', 'get_normal_max_versions.py', 'max', pkg],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                logging.error(f"Error running get_normal_max_versions.py for package: {pkg}")
                continue  # skip to next package

            output = result.stdout.strip()
            if output:
                # Assuming that "output" is a Python literal like ['max_version', filename]
                max_version_info = yaml.safe_load(output)
                max_version = max_version_info[0]

                # Compare the provided version and max version explicitly
                if Version(provided_version) < Version(max_version_info[0]):
                    logging.info(f"Using newer max version for {pkg}: {provided_version}→{max_version_info[0]}")
                    # update upgraded_versions and package_specs accordingly clearly
                    upgraded_versions[idx] = max_version_info[0]
                    input_packages[idx] = f"{pkg}=={max_version_info[0]}"
                else:
                    logging.info(f"Provided version for {pkg} ({provided_version}) is up-to-date or newer than max version ({max_version_info[0]}).")

        except Exception as e:
            logging.error(f"Exception running get_normal_max_versions.py for {pkg}: {e}")
    # explicitly regenerate package_specs string after possible version updates
    package_specs = ' '.join(input_packages)
    logging.info(f"Updated package specs after checking max versions: {package_specs}")
    print(f"\nUpdated package specs after max version check: {package_specs}")
else:
    logging.info("Skipping max version check as requested")
    print("\nSkipping max version check as requested")


# Function to load configuration from YAML file
def load_config(config_file):
    """Load configuration from a YAML file"""
    try:
        with open(config_file, 'r') as f:
            logging.info(f"Loading configuration from {config_file}")
            return yaml.safe_load(f)
    except Exception as e:
        error_msg = f"Error loading configuration from {config_file}: {e}"
        logging.error(error_msg)
        print(error_msg)
        return None

# Function to run commands in the virtual environment
def run_in_venv(command):
    """Run a command in the virtual environment"""
    try:
        # For Ubuntu, use the bash activate script
        activate_cmd = f"source {env_name}/bin/activate"
        
        # Full command with activation
        full_cmd = f"{activate_cmd} && {command}"
        
        logging.info(f"Running command in virtual environment: {command}")
        # Run the command in a shell
        result = subprocess.run(full_cmd, shell=True, executable='/bin/bash')
        
        if result.returncode != 0:
            error_msg = f"Command failed with return code {result.returncode}: {command}"
            logging.error(error_msg)
            print(error_msg)
        
        return result
    except Exception as e:
        error_msg = f"Exception while running command '{command}': {e}"
        logging.error(error_msg)
        print(error_msg)
        return None

try:
    print("Setting up environment with required dependencies...")
    logging.info("Starting environment setup process")
    
    # Read requirement files from files_config.yml
    config = load_config("files_config.yml")
    if not config or 'requirement_files' not in config or not config['requirement_files']:
        warning_msg = "Warning: Could not load requirement files from files_config.yml. Using default."
        logging.warning(warning_msg)
        print(warning_msg)
        requirement_file = "requirement_files/python3_dev_requirements.txt"
    else:
        logging.info(f"Requirement files found: {config['requirement_files']}")
        # Set requirement_file to the first requirement file in the list
        requirement_file = config['requirement_files'][0]
        print(f"Using requirement file from config: {requirement_file}")
    yml_file = "requirement_files/main.yml"
    env_name = "demo_myenv"  # Name of the virtual environment

    # Check if files exist
    for file_path in [requirement_file, yml_file]:
        if not os.path.isfile(file_path):
            error_msg = f"Required file not found: {file_path}"
            logging.error(error_msg)
            print(error_msg)
            sys.exit(1)

    # Run set_environment.py
    logging.info(f"Running set_environment.py with {requirement_file} and {yml_file}")
    subprocess.run(["python3", "set_environment.py", requirement_file, yml_file])

    # Install specific versions of packages in the virtual environment without dependencies
    logging.info(f"Installing specific package versions in virtual environment: {package_specs}")
    print("\nInstalling specific package versions in virtual environment (without dependencies)...")
    run_in_venv(f"pip3 install --no-deps {package_specs}")

    # Run dependency analysis in the virtual environment
    package_arg = ','.join(packages_to_update)
    logging.info(f"Analyzing dependencies for: {package_arg}")
    print(f"\nAnalyzing dependencies for: {package_arg}")
    run_in_venv(f"python3 update_dependency_rev_dependency.py {package_arg}")

    # Read the upgrade history from the temporary file
    upgrade_history = {}
    if os.path.exists('upgrade_history.json'):
        try:
            with open('upgrade_history.json', 'r') as f:
                upgrade_history = json.load(f)
            
            logging.info("Dependency upgrade history loaded successfully")
            print("\nDependency upgrade history loaded:")
            for pkg, versions in upgrade_history.items():
                log_msg = f"{pkg}: {versions['previous_version']} → {versions['upgraded_version']}"
                logging.info(log_msg)
                print(log_msg)
            
            # Clean up the temporary file
            # os.remove('upgrade_history.json')
        except Exception as e:
            error_msg = f"Error reading dependency upgrade history: {e}"
            logging.error(error_msg)
            print(error_msg)
    else:
        log_msg = "No dependency upgrade history found."
        logging.info(log_msg)
        print(log_msg)
    
    # Add input packages to upgrade history if they're not already there
    for idx, pkg in enumerate(packages_to_update):
        if pkg not in upgrade_history:
            # We already have the version information from input_packages
            version = upgraded_versions[idx]
            
            # Add to upgrade history
            upgrade_history[pkg] = {
                "previous_version": "Direct installation",
                "upgraded_version": version
            }
            
            log_msg = f"Added input package to history: {pkg}: Direct installation → {version}"
            logging.info(log_msg)
            print(log_msg)
    
    # Now upgrade_history contains both the data from the file and the input packages
    
    # Update requirement files with upgraded packages and compile them
    print("\n--- Updating requirement files with upgraded packages ---")
    logging.info("Starting to update requirement files with upgraded packages")
    
    # Get all requirement files from config
    all_requirement_files = []
    if config and 'requirement_files' in config:
        all_requirement_files = config['requirement_files']
    else:
        all_requirement_files = [requirement_file]  # Use the default one if config not available
    
    # Process each requirement file
    for req_file in all_requirement_files:
        logging.info(f"Processing requirement file: {req_file}")
        print(f"\nProcessing file: {req_file}")
        
        # Track which packages were updated in this file
        updated_packages = []
        
        # Check and update each package from upgrade_history in this file
        for pkg_name, versions in upgrade_history.items():
            # Skip packages that weren't actually upgraded
            if versions['previous_version'] == versions['upgraded_version']:
                continue
                
            # First check if package exists in this file and get its current version
            try:
                result = subprocess.run(
                    ['python3', 'get_normal_max_versions.py', 'get', pkg_name, req_file],
                    capture_output=True, text=True
                )
                
                # If package exists in this file
                if result.returncode == 0:
                    current_version = result.stdout.strip()
                    logging.info(f"Found {pkg_name} in {req_file} with version {current_version}")
                    
                    # Compare versions
                    if current_version and Version(current_version) < Version(versions['upgraded_version']):
                        # Update the package version in the file
                        logging.info(f"Updating {pkg_name} in {req_file} from {current_version} to {versions['upgraded_version']}")
                        update_result = subprocess.run(
                            ['python3', 'get_normal_max_versions.py', 'set', pkg_name, versions['upgraded_version'], req_file],
                            capture_output=True, text=True
                        )
                        
                        if update_result.returncode == 0:
                            updated_packages.append({
                                'name': pkg_name,
                                'previous_version': current_version,
                                'upgraded_version': versions['upgraded_version']
                            })
                            logging.info(f"Successfully updated {pkg_name} in {req_file}")
                        else:
                            logging.error(f"Failed to update {pkg_name} in {req_file}: {update_result.stderr}")
            except Exception as e:
                logging.error(f"Error checking/updating {pkg_name} in {req_file}: {e}")
        
        # If any packages were updated, compile the file
        if updated_packages:
            logging.info(f"Compiling updated requirement file: {req_file}")
            
            # Check if this is an .in file
            is_in_file = req_file.endswith('.in')
            
            try:
                if is_in_file:
                    # For .in files, use --allow-unsafe and let pip-tools create the output file automatically
                    logging.info(f"Compiling .in file with --allow-unsafe")
                    
                    # The output will automatically be named as the .in file but with .txt extension
                    compile_cmd = ['python3', '-m', 'piptools', 'compile', req_file, '--allow-unsafe']
                    compile_result = subprocess.run(
                        compile_cmd,
                        shell=False,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL
                    )
                    
                    # Check if the compiled file was created (replace .in with .txt)
                    expected_output = req_file[:-3] + '.txt'
                    if os.path.exists(expected_output):
                        logging.info(f"Successfully compiled {req_file} to {expected_output} (keeping file)")
                        # Print summary of updates for this file
                        print(f"\n{req_file} → {expected_output}")
                        for pkg in updated_packages:
                            print(f"{pkg['name']} ({pkg['previous_version']} → {pkg['upgraded_version']})")
                    else:
                        logging.error(f"Failed to compile {req_file}")
                        print(f"Failed to compile {req_file}. See log for details.")
                else:
                    # For non-.in files, use the original approach and delete the compiled file after
                    compiled_file = f"compiled_{os.path.basename(req_file)}"
                    
                    compile_cmd = ['python3', '-m', 'piptools', 'compile', req_file, f'--output-file={compiled_file}']
                    compile_result = subprocess.run(
                        compile_cmd,
                        shell=False,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL
                    )
                    
                    if os.path.exists(compiled_file):
                        logging.info(f"Successfully compiled {req_file} to {compiled_file}")
                        
                        # Print summary of updates for this file
                        print(f"\n{req_file}")
                        for pkg in updated_packages:
                            print(f"{pkg['name']} ({pkg['previous_version']} → {pkg['upgraded_version']})")
                        
                        # Delete the compiled file after processing
                        try:
                            os.remove(compiled_file)
                            logging.info(f"Deleted compiled file: {compiled_file}")
                        except Exception as e:
                            logging.warning(f"Failed to delete compiled file {compiled_file}: {e}")
                    else:
                        logging.error(f"Failed to compile {req_file}")
                        print(f"Failed to compile {req_file}. See log for details.")
            except Exception as e:
                logging.error(f"Error compiling {req_file}: {e}")
                print(f"Error compiling {req_file}: {e}")
        else:
            logging.info(f"No packages to update in {req_file}")
            print(f"No packages to update in {req_file}")

    # Update packages in YAML files
    if config and 'yml_files' in config:
        print("\n--- Updating packages in YAML files ---")
        logging.info("Starting to update packages in YAML files")
        
        for yml_file in config['yml_files']:
            if not os.path.isfile(yml_file):
                logging.warning(f"YAML file not found: {yml_file}")
                print(f"Warning: YAML file not found: {yml_file}")
                continue
                
            logging.info(f"Processing YAML file: {yml_file}")
            print(f"\nProcessing YAML file: {yml_file}")
            
            # Track which packages were updated in this file
            updated_packages = []
            unchanged_packages = []
            not_found_packages = []
            
            # Update each package from upgrade_history in this YAML file
            for pkg_name, versions in upgrade_history.items():
                # Skip packages that weren't actually upgraded
                if versions['previous_version'] == versions['upgraded_version']:
                    continue
                    
                # Run extract_install_pip_apt_from_yml.py to update the package version
                try:
                    logging.info(f"Attempting to update {pkg_name} to {versions['upgraded_version']} in {yml_file}")
                    result = subprocess.run(
                        ['python3', 'extract_install_pip_apt_from_yml.py', 'set', pkg_name, versions['upgraded_version'], yml_file],
                        capture_output=True, text=True
                    )
                    
                    # Parse the JSON result if available
                    result_data = None
                    for line in result.stdout.splitlines():
                        if line.startswith("RESULT: "):
                            try:
                                result_data = json.loads(line[8:])  # Skip "RESULT: " prefix
                                break
                            except json.JSONDecodeError:
                                pass
                    
                    if result_data:
                        if result_data["status"] == "updated":
                            updated_packages.append({
                                'name': pkg_name,
                                'previous_version': result_data.get("old_version", versions['previous_version']),
                                'upgraded_version': versions['upgraded_version']
                            })
                            logging.info(f"Successfully updated {pkg_name} in {yml_file}")
                        elif result_data["status"] == "unchanged":
                            unchanged_packages.append(pkg_name)
                            logging.info(f"{pkg_name} already at desired version in {yml_file}")
                        elif result_data["status"] == "not_found":
                            not_found_packages.append(pkg_name)
                            logging.info(f"{pkg_name} not found in {yml_file}")
                        else:
                            logging.error(f"Error updating {pkg_name} in {yml_file}: {result_data['message']}")
                    else:
                        # Fallback to the old string parsing if JSON result not found
                        if "Updated" in result.stdout:
                            updated_packages.append({
                                'name': pkg_name,
                                'previous_version': versions['previous_version'],
                                'upgraded_version': versions['upgraded_version']
                            })
                            logging.info(f"Successfully updated {pkg_name} in {yml_file}")
                        elif "already at desired version" in result.stdout:
                            unchanged_packages.append(pkg_name)
                            logging.info(f"{pkg_name} already at desired version in {yml_file}")
                        elif "not found" in result.stdout:
                            not_found_packages.append(pkg_name)
                            logging.info(f"{pkg_name} not found in {yml_file}")
                        else:
                            logging.warning(f"Unexpected output for {pkg_name} in {yml_file}: {result.stdout}")
                except Exception as e:
                    logging.error(f"Error updating {pkg_name} in {yml_file}: {e}")
            
            # Print summary of updates for this file
            print(f"\nSummary for {yml_file}:")
            if updated_packages:
                print("  Updated packages:")
                for pkg in updated_packages:
                    print(f"    {pkg['name']} ({pkg['previous_version']} → {pkg['upgraded_version']})")
            if unchanged_packages:
                print("  Already at desired version:")
                for pkg in unchanged_packages:
                    print(f"    {pkg}")
            if not_found_packages:
                print("  Not found in file:")
                for pkg in not_found_packages:
                    print(f"    {pkg}")
            if not (updated_packages or unchanged_packages or not_found_packages):
                print("  No packages processed")

    # Verify the installation in the virtual environment
    logging.info("Verifying installed package versions")
    print("\nVerifying installed package versions:")
    packages_to_verify = '|'.join(packages_to_update)
    run_in_venv(f"pip3 list | grep -E '{packages_to_verify}'")

    success_msg = "\nWrapper script completed successfully"
    logging.info(success_msg)
    print(success_msg)

except Exception as e:
    error_msg = f"Error in wrapper script: {str(e)}"
    logging.error(error_msg)
    logging.error(traceback.format_exc())
    print(f"{error_msg}\nCheck 'resolve_dependencies.log' for details.")
    sys.exit(1)

