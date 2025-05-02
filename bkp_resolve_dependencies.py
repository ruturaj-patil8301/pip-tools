import click
from pathlib import Path
from typing import Set
from pip._internal.req import InstallRequirement
from piptools.repositories import PyPIRepository
from piptools.resolver import BacktrackingResolver
from piptools.utils import (
    key_from_req,
    install_req_from_line
)
from piptools.cache import DependencyCache

def parse_requirements(filename: str) -> Set[InstallRequirement]:
    """Parse requirements from file."""
    requirements = set()
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                requirements.add(install_req_from_line(line))
    return requirements

def get_req_name(ireq: InstallRequirement) -> str:
    """Get requirement name safely."""
    if ireq.req:
        return ireq.req.name or ''
    return ''

def resolve_dependencies(input_file: str, output_file: str, cache_dir: str) -> None:
    """Resolve and pin dependencies from input file."""
    try:
        # Create cache directory
        cache_path = Path(cache_dir)
        cache_path.mkdir(exist_ok=True)

        # Parse input requirements
        requirements = parse_requirements(input_file)
        
        # Setup repository
        repository = PyPIRepository([], cache_dir=str(cache_path))
        
        # Create existing constraints dictionary
        existing_constraints = {}  # Empty dict since we're handling unpinned requirements
        
        # Create resolver
        resolver = BacktrackingResolver(
            constraints=requirements,
            existing_constraints=existing_constraints,
            repository=repository,
            prereleases=False
        )
        
        # Resolve dependencies
        results = resolver.resolve()
        
        # Write resolved requirements
        with open(output_file, 'w') as f:
            f.write("# Dependencies\n")
            # Sort requirements by package name
            sorted_results = sorted(results, key=lambda x: get_req_name(x))
            for req in sorted_results:
                if req.req:  # Check if req has a requirement object
                    f.write(f"{str(req.req)}\n")
            f.write("\n")
            
        click.echo(f"Successfully wrote resolved dependencies to {output_file}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

@click.command()
@click.option('--input-file', '-i', default='requirements.txt',
              help="Input requirements file")
@click.option('--output-file', '-o', default='new-requirements.txt',
              help="Output requirements file")
@click.option('--cache-dir', default=".dependency-cache",
              help="Directory to store dependency cache")
def main(input_file: str, output_file: str, cache_dir: str):
    """Resolve and pin dependencies from requirements file."""
    resolve_dependencies(input_file, output_file, cache_dir)

if __name__ == '__main__':
    main()
