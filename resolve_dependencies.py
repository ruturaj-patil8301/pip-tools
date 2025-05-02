import click
from pathlib import Path
from typing import Set, Tuple
from pip._internal.req import InstallRequirement
from piptools.repositories import PyPIRepository
from piptools.resolver import BacktrackingResolver
from piptools.utils import key_from_req, install_req_from_line
from pip._internal.exceptions import DistributionNotFound
from pip._vendor.resolvelib.resolvers import ResolutionImpossible  # Changed import path

def clean_requirement_line(line: str) -> str:
    """Remove comments and clean the requirement line."""
    # Split on '#' and take the first part (requirement)
    line = line.split('#')[0].strip()
    return line

def parse_requirements(filename: str) -> Set[InstallRequirement]:
    """Parse requirements from file with better error handling."""
    requirements = set()
    with open(filename) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line and not line.startswith('#'):
                try:
                    requirements.add(install_req_from_line(line))
                except Exception as e:
                    click.echo(f"Warning: Invalid requirement on line {line_num}: '{line}' ({str(e)})")
    return requirements

def get_req_name(ireq: InstallRequirement) -> str:
    """Get requirement name safely."""
    if ireq.req:
        return ireq.req.name or ''
    return ''

def resolve_dependencies(input_file: str, output_file: str, cache_dir: str) -> None:
    """Resolve and pin dependencies from input file."""
    temp_base_dir = "/var/lib/rubrik/staging/local/pip-temp"
    
    try:
        # Create base directory if it doesn't exist
        Path(temp_base_dir).mkdir(parents=True, exist_ok=True)
        
        # Parse input requirements
        requirements = parse_requirements(input_file)
        
        if not requirements:
            raise click.ClickException("No valid requirements found in input file")
        
        # Setup repository with temporary cache
        repository = PyPIRepository([], cache_dir=temp_base_dir)
        
        # Create resolver with increased max rounds
        resolver = BacktrackingResolver(
            constraints=requirements,
            existing_constraints={},
            repository=repository,
            prereleases=False,
            cache=None  # Added this to avoid potential cache issues
        )
        
        try:
            # Attempt to resolve with increased max rounds
            results = resolver.resolve(max_rounds=50)
            
            # Write resolved requirements
            with open(output_file, 'w') as f:
                f.write("# Dependencies\n")
                sorted_results = sorted(results, key=lambda x: get_req_name(x))
                for req in sorted_results:
                    if req.req:
                        f.write(f"{str(req.req)}\n")
            
            click.echo(f"Successfully wrote resolved dependencies to {output_file}")
            
        except ResolutionImpossible as e:
            click.echo("\nDetected conflicting dependencies:", err=True)
            if hasattr(e, 'causes'):
                for cause in e.causes:
                    click.echo(f"\nConflict: {cause}", err=True)
            else:
                click.echo(f"\nConflict details: {str(e)}", err=True)
                
            click.echo("\nSuggestions:", err=True)
            click.echo("1. Try updating problematic packages to newer versions")
            click.echo("2. Consider removing strict version pins where possible")
            click.echo("3. Check if all specified versions are actually required")
            raise click.Abort()
            
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
