import requests
from packaging.specifiers import SpecifierSet
from packaging.version import Version

CRYPT_TARGET = Version("42.0.8")
PACKAGE = "snowflake-connector-python"

def get_all_versions(package_name):
    """Fetch all released versions of the package from PyPI."""
    url = f"https://pypi.org/pypi/{package_name}/json"
    resp = requests.get(url)
    resp.raise_for_status()
    return list(resp.json()["releases"].keys())

def get_requires_dist(package_name, version):
    """Fetch the requires_dist field for a specific package version from PyPI."""
    url = f"https://pypi.org/pypi/{package_name}/{version}/json"
    resp = requests.get(url)
    if resp.status_code != 200:
        return []
    info = resp.json().get("info", {})
    return info.get("requires_dist", [])

def clean_specifier(specifier):
    """Clean and split the specifier correctly handling edge cases"""
    specifier = specifier.replace("(", "").replace(")", "")
    spec_parts = specifier.split(",")
    return SpecifierSet(spec_parts)

def find_compatible_versions():
    """Find and return all versions of the package compatible with the specified cryptography version."""
    print("SYLOR find_compatible_versions")
    compatible_versions = []
    versions = get_all_versions(PACKAGE)

    for version in sorted(versions, key=lambda v: Version(v)):
        requires = get_requires_dist(PACKAGE, version)
        for dep in requires:
            if dep.startswith("cryptography"):
                parts = dep.split(" ", 1)
                if len(parts) == 2:
                    try:
                        spec = clean_specifier(parts[1])
                        if CRYPT_TARGET in spec:
                            compatible_versions.append(version)
                    except Exception as e:
                        print(f"Could not parse {dep}: {e}")
                elif len(parts) == 1:
                    # No version constraint, assume it's compatible
                    compatible_versions.append(version)
                break
    return compatible_versions

if __name__ == "__main__":
    print("SYLOR Hello World")
    result = find_compatible_versions()
    if result:
        print(f"Versions of {PACKAGE} compatible with cryptography=={CRYPT_TARGET}:")
        for version in result:
            print(f" - {version}")
    else:
        print(f"No compatible versions found for cryptography=={CRYPT_TARGET}")
    print("SYLOR")
