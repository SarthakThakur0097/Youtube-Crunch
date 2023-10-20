import subprocess

# List all packages installed via pip
result = subprocess.run(["pip", "list"], text=True, capture_output=True)

# Split the result into lines and skip the header
lines = result.stdout.strip().split('\n')[2:]

# Uninstall each package
for line in lines:
    package_name = line.split()[0]
    subprocess.run(["pip", "uninstall", "-y", package_name])
