import os
import zipfile
from pathlib import Path

def create_delivery_zip():
    base_dir = Path(__file__).resolve().parent.parent
    zip_name = "EC_Sprint_4_2TSCOA_solucaofinal_LocaPredict_grupo_GKL.zip"
    zip_path = base_dir / zip_name

    excluded_dirs = {
        "node_modules",
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".venv",
        "venv",
        ".vscode",
        ".idea",
        "dist",
        "frontend/dist",
    }

    excluded_extensions = {
        ".pyc",
        ".pyo",
        ".pyd",
        ".db",
        ".sqlite3",
    }

    print(f"Creating delivery zip at: {zip_path}...")
    file_count = 0

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(base_dir):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            for file in files:
                file_path = Path(root) / file
                
                # Exclude zip itself and temp files
                if file_path == zip_path or file.endswith(".zip"):
                    continue
                if file_path.suffix.lower() in excluded_extensions:
                    continue
                if file == ".DS_Store" or file.startswith("~$"):
                    continue
                    
                arcname = file_path.relative_to(base_dir)
                zipf.write(file_path, arcname)
                file_count += 1

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"Success! {file_count} files packaged into {zip_name} ({size_mb:.2f} MB).")
    return zip_path

if __name__ == "__main__":
    create_delivery_zip()
