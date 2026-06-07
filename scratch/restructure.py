import os
import re
import shutil

core_modules = [
    "database", "Scraping", "backend", "session", 
    "auth", "logger", "analytics", "data_manager"
]
ui_modules = [
    "search_page", "detail_page", "ui_components", 
    "analytics_page", "compare_page", "favorites_page", 
    "history", "login_ui", "ui_settings"
]

# Create directories
os.makedirs("core", exist_ok=True)
os.makedirs("ui", exist_ok=True)

# Create __init__.py files so Python recognizes them as packages
with open("core/__init__.py", "w") as f: f.write("")
with open("ui/__init__.py", "w") as f: f.write("")

# Get all Python files in the root directory
all_files = [f for f in os.listdir(".") if f.endswith(".py") and os.path.isfile(f)]

# 1. Update imports in all Python files BEFORE moving them
for file in all_files:
    if file == "restructure.py":
        continue
    
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()

    # Update Core modules
    for mod in core_modules:
        content = re.sub(rf"\bfrom {mod}\b", f"from core.{mod}", content)
        content = re.sub(rf"(?m)^(\s*)import {mod}\b", rf"\1import core.{mod} as {mod}", content)

    # Update UI modules
    for mod in ui_modules:
        content = re.sub(rf"\bfrom {mod}\b", f"from ui.{mod}", content)
        content = re.sub(rf"(?m)^(\s*)import {mod}\b", rf"\1import ui.{mod} as {mod}", content)

    with open(file, "w", encoding="utf-8") as f:
        f.write(content)

# 2. Move files into their respective folders
for mod in core_modules:
    filename = f"{mod}.py"
    if os.path.exists(filename):
        shutil.move(filename, os.path.join("core", filename))

for mod in ui_modules:
    filename = f"{mod}.py"
    if os.path.exists(filename):
        shutil.move(filename, os.path.join("ui", filename))

print("Restructuring completed successfully! All UI files moved to 'ui/' and backend files to 'core/'.")
