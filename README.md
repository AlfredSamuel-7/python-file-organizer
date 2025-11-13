# Automated File Organizer & Duplicate Remover (Python)

A clean and reliable Python utility that organizes files, detects duplicates using SHA-256 hashing, and generates JSON/CSV reports. This tool is ideal for automating folder cleanup, managing download directories, and preventing storage waste.

---------------------------------------------------------
FEATURES
---------------------------------------------------------
- Organize files into extension-based folders (txt, jpg, pdf, no_ext)
- Detect duplicate files using SHA-256 hashing
- Remove duplicates while keeping the first or latest version
- Dry-run mode to preview actions safely
- JSON/CSV report generation
- Ignores sensitive directories like .git, node_modules, Library

---------------------------------------------------------
REQUIREMENTS
---------------------------------------------------------
- Python 3.8 or higher
- No external libraries required

---------------------------------------------------------
USAGE EXAMPLES
---------------------------------------------------------
Preview organize actions:
python main.py C:/path/to/folder --organize --dry-run

Organize files:
python main.py C:/path/to/folder --organize --move

Find duplicates:
python main.py C:/path/to/folder --duplicates

Remove duplicates (dry-run):
python main.py C:/path/to/folder --duplicates --remove-duplicates --dry-run

Remove duplicates (real):
python main.py C:/path/to/folder --duplicates --remove-duplicates

Generate report:
python main.py C:/path/to/folder --duplicates --remove-duplicates --report report.json

---------------------------------------------------------
HOW IT WORKS
---------------------------------------------------------
1. Scans all files in the target directory
2. Categorizes files by extension
3. Computes SHA-256 hashes to detect duplicate content
4. Moves or copies files into organized extension-based folders
5. Removes duplicates if requested
6. Generates a detailed JSON or CSV report

---------------------------------------------------------
SAFETY NOTES
---------------------------------------------------------
- Always run with --dry-run before actual changes
- Avoid running on system directories
- Keep backups of important files

---------------------------------------------------------
LICENSE
---------------------------------------------------------
MIT License — free to use, modify, and distribute.

---------------------------------------------------------
AUTHOR
---------------------------------------------------------
Developed by Alfred Samuel as part of a Python automation project showcasing file organization and scripting skills.
