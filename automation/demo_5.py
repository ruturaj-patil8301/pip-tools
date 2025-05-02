import yaml
import sys
from packaging.version import Version

def load_config(config_file):
    with open(config_file, 'r') as stream:
        return yaml.safe_load(stream)

def read_requirements(file_path):
    packages = {}
    try:
        with open(file_path, 'r') as fp:
            for line in fp:
                line = line.strip()
                if '==' in line:
                    pkg, ver = line.split('==')
                    packages[pkg.strip()] = ver.strip()
    except FileNotFoundError:
        pass
    return packages

def write_requirements(file_path, package_versions):
    with open(file_path, 'w') as fp:
        for pkg, ver in package_versions.items():
            fp.write(f"{pkg}=={ver}\n")

def get_package_version(file, package_name):
    packages = read_requirements(file)
    return packages.get(package_name)

def get_max_version_across_files(files, package_name):
    max_version = None
    file_with_max_version = None
    for file in files:
        packages = read_requirements(file)
        ver = packages.get(package_name)
        if ver:
            try:
                current_version = Version(ver)
                if (max_version is None) or (current_version > Version(max_version)):
                    max_version = ver
                    file_with_max_version = file
            except:
                continue
    if max_version:
        return [max_version, file_with_max_version]
    else:
        return [None, None]

def update_package_version_in_file(file, package_name, new_version):
    packages = read_requirements(file)
    if package_name in packages:
        packages[package_name] = new_version
        write_requirements(file, packages)
        return True
    else:
        return False

if __name__ == "__main__":
    config = load_config("files_config.yml")
    files = config['requirement_files']

    if len(sys.argv) < 2:
        print("\nUsage: python manage_existing_files.py [get|max|set] <arguments>\n")
        sys.exit(1)

    action = sys.argv[1]

    if action == "get":
        if len(sys.argv) != 4:
            print("Usage: python manage_existing_files.py get <package_name> <file>")
            sys.exit(1)
        _, _, package_name, file = sys.argv
        version = get_package_version(file, package_name)
        if version:
            print(f"{package_name} version in {file}: {version}")
        else:
            print(f"{package_name} not found in {file}")

    elif action == "max":
        if len(sys.argv) != 3:
            print("Usage: python manage_existing_files.py max <package_name>")
            sys.exit(1)
        _, _, package_name = sys.argv
        result = get_max_version_across_files(files, package_name)
        if result[0]:
            max_version, location = result
            print(f"[\"{max_version}\", \"{location}\"]")
        else:
            print(f"{package_name} not found in any files")

    elif action == "set":
        if len(sys.argv) != 5:
            print("Usage: python manage_existing_files.py set <package_name> <new_version> <file>")
            sys.exit(1)
        _, _, package_name, new_version, file = sys.argv
        successful = update_package_version_in_file(file, package_name, new_version)
        if successful:
            print(f"Updated {package_name} to version {new_version} in {file}")
        else:
            print(f"No changes made: {package_name} not found in {file}")

    else:
        print("Invalid action specified explicitly. Allowed: get|max|set")
