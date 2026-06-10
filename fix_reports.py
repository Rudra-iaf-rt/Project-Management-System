# fix_reports.py
import os

# Read the current file
file_path = 'apps/reports/views.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the problematic import
old_import = "from apps.projects.models import Project, Task"
new_import = "from apps.projects.models import Project\nfrom apps.tasks.models import Task"

if old_import in content:
    content = content.replace(old_import, new_import)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✓ Fixed apps/reports/views.py")
else:
    print("✓ File already fixed or pattern not found")

print("\nNow run: python manage.py check")