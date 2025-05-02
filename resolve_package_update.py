import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def read_requirements(filename: str) -> List[str]:
    """Read requirements from file, ignoring comments and empty lines."""
    requirements = []
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                requirements.append(line)
    return requirements

def parse_package_spec(spec: str) -> Tuple[str, str]:
    """Parse package specification into name and version."""
    try:
        package_name, version = spec.split('==')
        return package_name.strip(), version.strip()
    except ValueError:
        raise ValueError(f"Invalid package specification: {spec}")

def install_package_with_version(package_name: str, version: str) -> bool:
    """Install a specific version of a package."""
    module_with_version = f"{package_name}=={version}"
    
    for attempt in range(3):
        try:
            subprocess.check_call([
                sys.executable, 
                '-m', 
                'pip', 
                'install', 
                '--no-deps',  # Don't install dependencies yet
                module_with_version
            ])
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(f"Attempt {attempt + 1} failed to install {module_with_version}: {e}")
            if attempt < 2:
                continue
    return False

def get_dependency_tree() -> Dict:
    """Get dependency tree using pipdeptree."""
    try:
        # Ensure pipdeptree is installed
        subprocess.check_call([
            sys.executable, 
            '-m', 
            'pip', 
            'install', 
            'pipdeptree'
        ])
        
        # Get dependency tree
        result = subprocess.run(
            [sys.executable, "-m", "pipdeptree", "-j"],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get dependency tree: {e}")
        return {}

def find_and_get_dependencies(package_name: str, dep_graph: List) -> Dict[str, str]:
    """Find all dependencies for a package."""
    dep_map = {}
    
    for child in dep_graph:
        package_key = child['package']['key']
        if package_key.casefold() == package_name.casefold():
            # Add the package itself
            dep_map[package_key] = child['package']['installed_version']
            
            # Add its dependencies
            for dep in child['dependencies']:
                dep_name = dep['package_name']
                dep_version = dep['installed_version']
                if dep_version == '?':
                    dep_version = dep['required_version'][2:]
                    if "!" in dep_version:
                        dep_version = dep_version.split('!')[0]
                
                dep_map[dep_name] = dep_version
                # Recursively get nested dependencies
                nested_deps = find_and_get_dependencies(dep_name, dep_graph)
                dep_map.update(nested_deps)
    
    return dep_map

def resolve_dependencies(input_file: str, output_file: str) -> bool:
    """
    Resolve dependencies from input file and write to output file.
    Returns True if successful, False otherwise.
    """
    try:
        # Read current requirements
        current_reqs = read_requirements(input_file)
        if not current_reqs:
            logger.error(f"No valid requirements found in {input_file}")
            return False
        
        # Install each package without dependencies first
        for req in current_reqs:
            package_name, version = parse_package_spec(req)
            if not install_package_with_version(package_name, version):
                logger.error(f"Failed to install {req}")
                return False
        
        # Get complete dependency tree
        dep_tree = get_dependency_tree()
        if not dep_tree:
            logger.error("Failed to generate dependency tree")
            return False
        
        # Collect all dependencies
        all_dependencies = {}
        for req in current_reqs:
            package_name, _ = parse_package_spec(req)
            deps = find_and_get_dependencies(package_name, dep_tree)
            all_dependencies.update(deps)
        
        # Write resolved dependencies
        with open(output_file, 'w') as f:
            f.write("# Dependencies updated\n")
            for package_name, version in sorted(all_dependencies.items()):
                f.write(f"{package_name}=={version}\n")
        
        logger.info(f"Successfully wrote resolved dependencies to {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error resolving dependencies: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Resolve package dependencies from input file"
    )
    parser.add_argument(
        '--input-file',
        default='conflicting_deps.txt',
        help='Input requirements file'
    )
    parser.add_argument(
        '--output-file',
        default='resolved_conflicts.txt',
        help='Output requirements file'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if not resolve_dependencies(args.input_file, args.output_file):
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
