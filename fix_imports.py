import os
import re

BASE_DIR = "src/secondbrain"

def convert_import(line, current_path):
    # Match imports like: from secondbrain.module.submodule import something
    pattern = r"from secondbrain(\.[\w\.]+)? import (.+)"
    match = re.match(pattern, line.strip())
    if not match:
        return line
    
    module_path = match.group(1) or ""
    imported_items = match.group(2)
    
    # Calculate relative level based on current_path depth inside secondbrain
    depth = current_path.count(os.sep)
    
    # Build relative import prefix (e.g., .. or ...)
    relative_prefix = "." * (depth + 1)  # +1 because we are inside secondbrain folder
    
    # Remove leading dot from module_path if present
    module_path = module_path.lstrip(".")
    
    # Construct relative import line
    if module_path:
        new_line = f"from {relative_prefix}{module_path} import {imported_items}\n"
    else:
        new_line = f"from {relative_prefix} import {imported_items}\n"
    
    return new_line

def fix_imports_in_file(file_path):
    rel_path = os.path.relpath(file_path, BASE_DIR)
    dir_path = os.path.dirname(rel_path)
    
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    new_lines = []
    changed = False
    
    for line in lines:
        new_line = convert_import(line, dir_path)
        if new_line != line:
            changed = True
        new_lines.append(new_line)
    
    if changed:
        print(f"Fixing imports in: {file_path}")
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

def main():
    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                fix_imports_in_file(file_path)
    print("Import fix completed.")

if __name__ == "__main__":
    main()
