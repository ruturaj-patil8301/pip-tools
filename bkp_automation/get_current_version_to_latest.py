import subprocess
import sys
from packaging import version

def get_versions(package_name):
    # Run the pip3 index versions command and capture output
    result = subprocess.run(
        ['pip3', 'index', 'versions', package_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )
    return result.stdout

def parse_versions(output):
    lines = output.splitlines()
    installed = None
    versions = []
    for line in lines:
        if line.startswith('Available versions:'):
            # Extract and split versions
            versions = [v.strip() for v in line.split(':', 1)[1].split(',')]
        elif line.strip().startswith('INSTALLED:'):
            installed = line.split(':', 1)[1].strip()
    return installed, versions

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <package_name>")
        sys.exit(1)
    package_name = sys.argv[1]
    output = get_versions(package_name)
    installed, versions = parse_versions(output)
    if not installed:
        print(f"No installed version found for {package_name}.")
        sys.exit(1)
    newer_versions = [v for v in versions if version.parse(v) > version.parse(installed)]
    print(f"Installed version: {installed}")
    print("Available newer versions:")
    for v in newer_versions:
        print(v)
    print(newer_versions)

if __name__ == '__main__':
    main()

