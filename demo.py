import re
from packaging import version

package_data = """
Flask==3.0.2
├── Werkzeug [required: >=3.0.0, installed: 0.15.5]
├── Jinja2 [required: >=3.1.2, installed: 2.10.3]
│   └── MarkupSafe [required: >=0.23, installed: 2.0.1]
├── itsdangerous [required: >=2.1.2, installed: 0.24]
├── click [required: >=8.1.3, installed: 8.1.8]
└── blinker [required: >=1.6.2, installed: ?]
"""

def parse_package_data(data):
    packages = []
    lines = data.strip().split('\n')
    
    for line in lines:
        match = re.match(r'^[├└│─]*\s*(\S+)\s\[required:\s*([^,]+),\s*installed:\s*(\S+)\]', line)
        if match:
            name = match.group(1)
            required_version = match.group(2).strip()
            installed_version = match.group(3).strip()
            packages.append((name, required_version, installed_version))
    
    return packages

def compare_versions(required, installed):
    if installed == '?':
        return 'unknown'
    
    # Extract version number from required version constraint
    required_version = re.match(r'^[^\d]*([\d\.]+)', required).group(1)
    
    if version.parse(installed) < version.parse(required_version):
        return 'problematic'
    return 'ok'

def highlight_packages(packages):
    for name, required_version, installed_version in packages:
        status = compare_versions(required_version, installed_version)
        if status == 'problematic':
            print(f'{name}: required {required_version}, installed {installed_version} [PROBLEMATIC]')
        elif status == 'unknown':
            print(f'{name}: required {required_version}, installed {installed_version} [UNKNOWN]')
        else:
            print(f'{name}: required {required_version}, installed {installed_version} [OK]')

package_list = parse_package_data(package_data)
highlight_packages(package_list)
