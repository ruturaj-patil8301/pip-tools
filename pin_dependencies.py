import click
from pathlib import Path
from typing import Set, Optional, Dict, List, Tuple
import subprocess
import json
import sys
import re
import logging

# Set up logging at the top of the file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def read_requirements(filename: str) -> List[str]:
    """Read requirements from file, preserving their exact format."""
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def update_requirement(requirements: List[str], package_spec: str) -> List[str]:
    """Update specific package in requirements while preserving others."""
    package_name = package_spec.split('==')[0].lower()
    updated_reqs = []
    
    # Add all requirements except the package being updated
    for req in requirements:
        # Skip empty lines and comments
        if not req.strip() or req.startswith('#'):
            continue
            
        current_package = req.split('==')[0].lower()
        if current_package != package_name:
            updated_reqs.append(req)
    
    # Add the new package version
    updated_reqs.append(package_spec)
    
    # Sort requirements for consistency
    return sorted(updated_reqs)

def run_command(cmd: List[str]) -> Tuple[str, str, int]:
    """Run a command and return stdout, stderr, and return code."""
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate()
    return stdout, stderr, process.returncode

def check_package_compatibility(package_spec: str, requirements: List[str]) -> Tuple[bool, str]:
    """Check if package is compatible with current requirements."""
    # Extract package name and version
    package_name = package_spec.split('==')[0].lower()
    
    # Filter out any existing version of the same package
    filtered_reqs = [
        req for req in requirements 
        if req.split('==')[0].lower() != package_name
    ]
    
    # Create a temporary environment to test compatibility
    cmd = [sys.executable, "-m", "pip", "install", "--dry-run"]
    cmd.extend([package_spec] + filtered_reqs)
    
    stdout, stderr, return_code = run_command(cmd)
    return return_code == 0, stderr

def get_package_dependencies(package_spec: str) -> Dict[str, List[Dict]]:
    """Get direct and reverse dependencies for a package using pipdeptree."""
    package_name = package_spec.split('==')[0]
    logger.info(f"Getting dependencies for {package_spec}")
    
    # First try to install the new version with --no-deps
    install_cmd = [sys.executable, "-m", "pip", "install", "--no-deps", package_spec]
    logger.info(f"Running install command: {' '.join(install_cmd)}")
    stdout, stderr, return_code = run_command(install_cmd)
    if return_code != 0:
        logger.error(f"Failed to install {package_spec} with --no-deps: {stderr}")
        return {"direct": [], "reverse": [], "conflicts": []}
    
    # Get dependency information using pipdeptree
    cmd = ["pipdeptree", "-p", package_name, "--json"]
    logger.info(f"Running pipdeptree command: {' '.join(cmd)}")
    stdout, stderr, return_code = run_command(cmd)
    logger.debug(f"pipdeptree output: {stdout}")
    logger.debug(f"pipdeptree stderr: {stderr}")
    
    # Also get reverse dependencies
    cmd_reverse = ["pipdeptree", "-r", "-p", package_name, "--json"]
    logger.info(f"Running reverse pipdeptree command: {' '.join(cmd_reverse)}")
    stdout_reverse, stderr_reverse, return_code_reverse = run_command(cmd_reverse)
    logger.debug(f"reverse pipdeptree output: {stdout_reverse}")
    logger.debug(f"reverse pipdeptree stderr: {stderr_reverse}")
    
    try:
        direct_deps = []
        reverse_deps = []
        conflicts = []
        
        # Parse direct dependencies
        if stdout:
            logger.info("Parsing direct dependencies")
            data = json.loads(stdout)
            logger.debug(f"Parsed JSON data: {data}")
            if isinstance(data, list) and data:
                for pkg in data:
                    if pkg.get("package_name", "").lower() == package_name.lower():
                        for dep in pkg.get("dependencies", []):
                            direct_deps.append({
                                "name": dep["package_name"],
                                "required_version": dep.get("required_version", "")
                            })
                            logger.info(f"Found direct dependency: {dep['package_name']} {dep.get('required_version', '')}")
        
        # Parse reverse dependencies
        if stdout_reverse:
            logger.info("Parsing reverse dependencies")
            data_reverse = json.loads(stdout_reverse)
            logger.debug(f"Parsed reverse JSON data: {data_reverse}")
            if isinstance(data_reverse, list):
                for pkg in data_reverse:
                    pkg_name = pkg.get("package_name", "")
                    pkg_version = pkg.get("installed_version", "")
                    
                    for dep in pkg.get("dependencies", []):
                        if dep["package_name"].lower() == package_name.lower():
                            dep_info = {
                                "name": pkg_name,
                                "version": pkg_version,
                                "constraint": dep.get("required_version", "")
                            }
                            reverse_deps.append(dep_info)
                            logger.info(f"Found reverse dependency: {pkg_name} {pkg_version} requires {package_name}{dep.get('required_version', '')}")
                            
                            # Check for version conflicts
                            if dep.get("required_version"):
                                from pkg_resources import Requirement, parse_version
                                try:
                                    req = Requirement.parse(f"{package_name}{dep['required_version']}")
                                    new_version = parse_version(package_spec.split('==')[1])
                                    if new_version not in req:
                                        conflicts.append(dep_info)
                                        logger.warning(f"Found version conflict: {pkg_name} {pkg_version} requires {package_name}{dep['required_version']}")
                                except Exception as e:
                                    logger.debug(f"Error checking version conflict: {e}")
        
        logger.info(f"Found {len(direct_deps)} direct dependencies, {len(reverse_deps)} reverse dependencies, and {len(conflicts)} conflicts")
        return {
            "direct": direct_deps,
            "reverse": reverse_deps,
            "conflicts": conflicts
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing pipdeptree JSON output: {e}")
        logger.error(f"Raw stdout: {stdout}")
        return {"direct": [], "reverse": [], "conflicts": []}
    except Exception as e:
        logger.error(f"Error processing dependencies: {e}")
        logger.error(f"Exception type: {type(e)}")
        return {"direct": [], "reverse": [], "conflicts": []}

def analyze_conflicts(package_spec: str, requirements: List[str]) -> List[str]:
    """Analyze dependency conflicts using pipdeptree and return suggestions."""
    logger.info(f"Analyzing conflicts for {package_spec}")
    suggestions = []
    deps = get_package_dependencies(package_spec)
    package_name = package_spec.split('==')[0]
    package_version = package_spec.split('==')[1]
    
    logger.info(f"Current requirements: {requirements}")
    
    if deps["conflicts"]:
        suggestions.append(f"\nConflicting dependencies detected for {package_spec}:")
        for conflict in deps["conflicts"]:
            conflict_msg = f"  - {conflict['name']} {conflict['version']} requires {package_name}{conflict['constraint']}"
            suggestions.append(conflict_msg)
            logger.info(f"Found conflict: {conflict_msg}")
        
        # Check which conflicting packages are in requirements
        conflict_names = [c["name"] for c in deps["conflicts"]]
        logger.info(f"Looking for conflicts with packages: {conflict_names}")
        
        req_conflicts = [
            req for req in requirements 
            if req.split('==')[0] in conflict_names
        ]
        logger.info(f"Found conflicting requirements: {req_conflicts}")
        
        if req_conflicts:
            suggestions.append("\nPackages in requirements.txt that need updating:")
            for req in req_conflicts:
                pkg_name = req.split('==')[0]
                logger.info(f"Checking for compatible versions of {pkg_name}")
                
                # Try to find compatible versions using pip
                cmd = [
                    sys.executable, "-m", "pip", "index", "versions", pkg_name,
                    "--pre", "--all"
                ]
                logger.info(f"Running pip index versions command: {' '.join(cmd)}")
                stdout, _, _ = run_command(cmd)
                
                latest_compatible = None
                if stdout:
                    versions = re.findall(r"Available versions: (.+)", stdout)
                    if versions:
                        version_list = versions[0].split(", ")
                        logger.info(f"Found versions for {pkg_name}: {version_list}")
                        for version in version_list:
                            version = version.strip()
                            logger.info(f"Testing compatibility of {pkg_name}=={version}")
                            # Check if this version is compatible with new cryptography
                            test_cmd = [
                                sys.executable, "-m", "pip", "install",
                                f"{pkg_name}=={version}", package_spec,
                                "--dry-run"
                            ]
                            _, _, return_code = run_command(test_cmd)
                            if return_code == 0:
                                latest_compatible = version
                                logger.info(f"Found compatible version: {pkg_name}=={version}")
                                break
                
                if latest_compatible:
                    msg = f"  - Update {pkg_name} to version {latest_compatible}"
                    suggestions.append(msg)
                    logger.info(msg)
                    # Update the requirement in the list
                    idx = requirements.index(req)
                    requirements[idx] = f"{pkg_name}=={latest_compatible}"
                else:
                    msg = f"  - {req} (No compatible version found)"
                    suggestions.append(msg)
                    logger.warning(msg)
    else:
        logger.info("No conflicts detected")
    
    return suggestions, requirements

@click.command()
@click.option('--input-file', '-i', default='requirements.txt',
              help="Input requirements file")
@click.option('--package-spec', '-p', required=True,
              help="Package specification to update (e.g., 'cryptography==42.0.8')")
@click.option('--output-file', '-o', default='resolved-requirements.txt',
              help="Output requirements file")
@click.option('--verbose', '-v', is_flag=True,
              help="Enable verbose logging")
def main(input_file: str, package_spec: str, output_file: str, verbose: bool):
    """Update package version while preserving other requirements."""
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    try:
        # Read existing requirements
        current_requirements = read_requirements(input_file)
        logger.debug(f"Read requirements from {input_file}: {current_requirements}")
        
        # Get package name for logging
        package_name = package_spec.split('==')[0]
        current_version = next(
            (req.split('==')[1] for req in current_requirements 
             if req.split('==')[0].lower() == package_name.lower()),
            None
        )
        
        if current_version:
            logger.info(f"Found existing {package_name}=={current_version}, attempting to upgrade to {package_spec}")
        
        # Analyze conflicts and get updated requirements
        suggestions, updated_requirements = analyze_conflicts(package_spec, current_requirements)
        if suggestions:
            logger.info("Dependency analysis suggestions:")
            for suggestion in suggestions:
                logger.info(suggestion)
        
        # Update the target package version
        final_requirements = update_requirement(updated_requirements, package_spec)
        logger.debug(f"Final requirements list: {final_requirements}")
        
        # Write updated requirements
        with open(output_file, 'w') as f:
            f.write(f"# Dependencies updated: {package_spec}\n")
            for req in final_requirements:
                f.write(req + "\n")
        
        logger.info(f"Successfully updated {package_name} and its dependencies in {output_file}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise click.Abort()

if __name__ == '__main__':
    main()
