import sys
import yaml
from packaging.version import Version, InvalidVersion

def read_config(config_file):
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def clean_version(version_part):
    return version_part.strip().strip('"\' ')

def extract_version_from_txt_or_in(filename, package_name):
    try:
        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()
                # Dependencies are exactly package_name == version
                if line.lower().startswith(package_name.lower() + '=='):
                    # Explicitly split at '==' only
                    parts = line.split('==', 1)
                    if len(parts) == 2:
                        _, ver = parts
                        return clean_version(ver)
    except FileNotFoundError:
        pass
    return None

def extract_version_from_yml(filename, package_name):
    try:
        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith('name:'):
                    _, rest = line.split(':', 1)
                    rest = rest.strip().strip('"\'')  
                    if rest.lower().startswith(package_name.lower()):
                        for sep in ['==', '>=', '<=', '!=', '~=', '>']:
                            if sep in rest:
                                pkg, ver = rest.split(sep, 1)
                                if pkg.strip().lower() == package_name.lower():
                                    return clean_version(ver)
    except FileNotFoundError:
        pass
    return None

def get_versions(config, package_name):
    version_mapping = {}
    files_to_check = config.get('txt_files', []) + config.get('in_files', []) + config.get('yml_files', [])

    for filename in files_to_check:
        version = None
        if filename.endswith(('.txt', '.in')):
            version = extract_version_from_txt_or_in(filename, package_name)
        elif filename.endswith(('.yml', '.yaml')):
            version = extract_version_from_yml(filename, package_name)

        if version:
            version_mapping[filename] = version

    return version_mapping

def get_max_version(version_mapping):
    valid_versions = []
    for ver in version_mapping.values():
        try:
            valid_versions.append(Version(ver))
        except InvalidVersion:
            pass
    return str(max(valid_versions)) if valid_versions else None

def main(config_file, package_name):
    config = read_config(config_file)
    mapping = get_versions(config, package_name)

    if not mapping:
        print(f"No version data found for '{package_name}'.")
        sys.exit(0)

    max_version = get_max_version(mapping)

    print("\nFile-to-Version Mapping found:")
    for f, v in mapping.items():
        print(f"{f}: {v}")

    print(f"\nMax version across all files for '{package_name}': {max_version}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python3 {sys.argv[0]} <config.yml> <package_name>")
        sys.exit(1)

    config_file, package_name = sys.argv[1], sys.argv[2]
    main(config_file, package_name)
