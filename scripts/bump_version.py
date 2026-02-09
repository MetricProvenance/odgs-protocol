
import sys
import re
import json
import os

# Paths relative to script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

FILES = {
    "pyproject": os.path.join(REPO_ROOT, "pyproject.toml"),
    "package": os.path.join(REPO_ROOT, "package.json"),
    "init": os.path.join(REPO_ROOT, "src", "odgs", "__init__.py")
}

def bump_version(new_version):
    print(f"🚀 Bumping ODGS Protocol to version: {new_version}")

    # 1. Update pyproject.toml
    # Pattern: version = "x.y.z"
    with open(FILES["pyproject"], "r") as f:
        content = f.read()
    
    new_content = re.sub(r'version = "[0-9]+\.[0-9]+\.[0-9]+"', f'version = "{new_version}"', content)
    
    with open(FILES["pyproject"], "w") as f:
        f.write(new_content)
    print(f"  ✅ Updated pyproject.toml")

    # 2. Update package.json
    with open(FILES["package"], "r") as f:
        pkg = json.load(f)
    
    pkg["version"] = new_version
    
    with open(FILES["package"], "w") as f:
        json.dump(pkg, f, indent=2)
        # Add newline at EOF
        f.write("\n")
    print(f"  ✅ Updated package.json")

    # 3. Update src/odgs/__init__.py
    # We might need to add a __version__ variable if it doesn't exist
    init_path = FILES["init"]
    with open(init_path, "r") as f:
        init_lines = f.readlines()
    
    # Check if __version__ exists
    version_line_index = -1
    for i, line in enumerate(init_lines):
        if line.startswith("__version__"):
            version_line_index = i
            break
            
    if version_line_index != -1:
        init_lines[version_line_index] = f'__version__ = "{new_version}"\n'
    else:
        init_lines.append(f'\n__version__ = "{new_version}"\n')
        
    with open(init_path, "w") as f:
        f.writelines(init_lines)
    print(f"  ✅ Updated src/odgs/__init__.py")
    
    print("\n✨ Version Lock Complete.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 bump_version.py <new_version>")
        sys.exit(1)
    
    new_ver = sys.argv[1]
    # Simple semantic version check regex
    if not re.match(r"^\d+\.\d+\.\d+$", new_ver):
        print("Error: Version must be in format X.Y.Z (e.g. 2.1.0)")
        sys.exit(1)
        
    bump_version(new_ver)
