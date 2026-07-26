import os

# Plik wyjściowy
OUTPUT_FILE = "calosc_repo.txt"

# Foldery i rozszerzenia do zignorowania
IGNORE_DIRS = {'.git', 'venv', '.venv', '__pycache__', '.idea', '.vscode'}
ALLOWED_EXTENSIONS = {'.py', '.md', '.json', '.yml', '.yaml'}

with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
    for root, dirs, files in os.walk('.'):
        # Pomijaj ukryte/niechciane foldery
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in ALLOWED_EXTENSIONS and file != 'scal_repo.py':
                filepath = os.path.join(root, file)
                outfile.write(f"\n{'='*50}\n")
                outfile.write(f"PLIK: {filepath}\n")
                outfile.write(f"{'='*50}\n\n")
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                        outfile.write("\n")
                except Exception as e:
                    outfile.write(f"[Błąd odczytu pliku: {e}]\n")

print(f"Gotowe! Cały kod został scalony do pliku: {OUTPUT_FILE}")