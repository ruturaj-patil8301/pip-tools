from pathlib import Path
import collections
from typing import Set, Dict, Mapping
import click
import logging
from pip._vendor.packaging.utils import canonicalize_name
from pip._internal.commands import create_command
from pip._internal.network.session import PipSession
from pip._internal.req.constructors import install_req_from_line as pip_install_req_from_line

# Use pip-tools compatibility layer instead of direct pip imports
from piptools._compat.pip_compat import InstallRequirement
from piptools.cache import DependencyCache
from piptools.repositories.pypi import PyPIRepository
from piptools.utils import (
    key_from_req,
    install_req_from_line
)
from piptools.resolver import BacktrackingResolver

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_repository(cache_dir: Path) -> PyPIRepository:
    """Create a PyPIRepository instance with proper configuration."""
    try:
        pip_args = ['--cache-dir', str(cache_dir)]
        repository = PyPIRepository(pip_args, cache_dir=str(cache_dir))
        return repository
    
    except Exception as e:
        logger.error(f"Error creating repository: {str(e)}")
        raise

def get_dependencies(package_spec: str, cache_dir: Path) -> Set[str]:
    """Get direct dependencies of a package."""
    try:
        repository = create_repository(cache_dir)
        ireq = install_req_from_line(package_spec)
        
        if not ireq.is_pinned:
            raise click.BadParameter("Package must be pinned (e.g., package==1.2.3)")
        
        logger.debug(f"Getting dependencies for {package_spec}")
        
        # Create a resolver
        resolver = BacktrackingResolver(
            constraints=[ireq],
            existing_constraints={},
            repository=repository
        )
        
        # Get dependencies using the resolver
        results = resolver.resolve()
        
        # Filter out the package itself from the results
        package_name = canonicalize_name(ireq.name)
        dependencies = {
            str(req.req) for req in results 
            if canonicalize_name(req.name) != package_name
        }
        
        logger.debug(f"Found dependencies: {dependencies}")
        return dependencies
    
    except Exception as e:
        logger.error(f"Error getting dependencies: {str(e)}")
        raise

def get_reverse_dependencies(package_spec: str, cache_dir: Path) -> Set[str]:
    """Get packages that depend on the given package."""
    try:
        cache = DependencyCache(cache_dir=cache_dir)
        
        # First, get the normalized package name
        ireq = install_req_from_line(package_spec)
        package_name = canonicalize_name(ireq.name)
        
        # Create a mapping of package names to their dependencies
        reverse_deps = set()
        
        # Iterate through the cache data to find packages that depend on our target
        cache_data = cache.cache if hasattr(cache, 'cache') else {}
        for pkg_name, pkg_deps in cache_data.items():
            for version_and_extras, deps in pkg_deps.items():
                if any(package_name == canonicalize_name(dep.split('==')[0]) for dep in deps):
                    reverse_deps.add(pkg_name)
        
        return reverse_deps
    
    except Exception as e:
        logger.error(f"Error getting reverse dependencies: {str(e)}")
        raise

@click.command()
@click.argument('package_spec')
@click.option('--cache-dir', type=click.Path(), default=".dependency-cache",
              help="Directory to store dependency cache")
def main(package_spec: str, cache_dir: str):
    """
    Show dependencies and reverse dependencies for a Python package.
    
    PACKAGE_SPEC should be in the format: package==version
    Example: requests==2.28.1
    """
    cache_path = Path(cache_dir)
    cache_path.mkdir(exist_ok=True)
    
    click.echo(f"\nAnalyzing {package_spec}...")
    
    try:
        # Get direct dependencies
        click.echo("\nDirect Dependencies:")
        deps = get_dependencies(package_spec, cache_path)
        if deps:
            for dep in sorted(deps):
                click.echo(f"  • {dep}")
        else:
            click.echo("  No direct dependencies found")
            
        # Get reverse dependencies
        click.echo("\nReverse Dependencies (packages that depend on this):")
        reverse_deps = get_reverse_dependencies(package_spec, cache_path)
        if reverse_deps:
            for rev_dep in sorted(reverse_deps):
                click.echo(f"  • {rev_dep}")
        else:
            click.echo("  No reverse dependencies found in cache")
            
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    main()
