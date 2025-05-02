import subprocess

#packages_to_resolve = ["flask", "requests", "django"]
packages_to_resolve = ["cryptography","flask"]
#packages_to_resolve = ["flask"]
#subprocess.run(["python3", "resolve_dependencies.py"] + packages_to_resolve)
package_arg = ','.join(packages_to_resolve)
subprocess.run(["python3", "update_dependency_rev_dependency.py", package_arg])
