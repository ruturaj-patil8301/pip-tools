import requests
from packaging.specifiers import SpecifierSet
from packaging.version import Version

#DEPENDENT_PACKAGE = Version("3.7.1")
DEPENDENT_PACKAGE = Version("42.0.8")
#DEPENDENT_PACKAGE = Version("3.0.3")
#DEPENDENT_PACKAGE_NAME = "snowflake-connector-python"
DEPENDENT_PACKAGE_NAME = "cryptography"
#DEPENDENT_PACKAGE_NAME = "werkzeug"
#DEPENDENCY = "pyopenssl"
DEPENDENCY = "snowflake-connector-python"
#DEPENDENCY = "MarkupSafe"

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
    #print(resp.json().get('info').get('requires_dist'))
    #print(resp.json().get('info'))
    if resp.status_code != 200:
        return []
    info = resp.json().get("info", {})
    return info.get("requires_dist", [])

def find_compatible_versions():
    """Find and return all versions of the package compatible with the specified DEPENDENT version."""
    print("SYLOR find_compatible_versions")
    compatible_versions = []
    versions = get_all_versions(DEPENDENCY)

    for version in sorted(versions, key=lambda v: Version(v)):
        requires = get_requires_dist(DEPENDENCY, version)
        if not requires:
            continue
        for dep in requires:
            if DEPENDENT_PACKAGE_NAME in dep:
                parts = dep.split(" ", 1)
                if len(parts) == 2:
                    try:
                        spec = SpecifierSet(parts[1])
                        if DEPENDENT_PACKAGE in spec:
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
        print(f"Versions of {DEPENDENCY} compatible with {DEPENDENT_PACKAGE_NAME}=={DEPENDENT_PACKAGE}:")
        for version in result:
            print(f" - {version}")
    else:
        print(f"No compatible versions found for {DEPENDENT_PACKAGE_NAME}=={DEPENDENT_PACKAGE}")
    print("SYLOR")
