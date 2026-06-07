import os

with open("main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_main_lines = []
data_manager_lines = [
    "import os\n",
    "import re\n",
    "import json\n",
    "\n",
    "from backend import BackendManager\n",
    "\n",
    "try:\n",
    "    from Scraping import KosScraper\n",
    "except Exception:\n",
    "    KosScraper = None\n",
    "\n"
]

in_controller = False
for i, line in enumerate(lines):
    line_num = i + 1
    
    # Exclude imports that will be moved
    if line_num in [2, 3, 4, 11, 25, 26, 27, 28]:
        continue
        
    if line.startswith("class IntegrationController:"):
        in_controller = True
        
    if in_controller:
        if line.startswith("class App(QMainWindow):"):
            in_controller = False
            new_main_lines.append(line)
        else:
            data_manager_lines.append(line)
    else:
        # Add import for IntegrationController right after sys
        if line_num == 1:
            new_main_lines.append(line)
            new_main_lines.append("from data_manager import IntegrationController\n")
        else:
            new_main_lines.append(line)

with open("data_manager.py", "w", encoding="utf-8") as f:
    f.writelines(data_manager_lines)

with open("main.py", "w", encoding="utf-8") as f:
    f.writelines(new_main_lines)

print("Refactoring complete.")
