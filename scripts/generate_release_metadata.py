import os
import hashlib
import json

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Critical files to generate checksums for
files_to_hash = [
    "install.bat",
    "pyproject.toml",
    "requirements.txt",
    "scripts/install.py",
    "scripts/validate_system.py",
    "src/backend/app/main.py",
    "src/frontend/dist/index.html",
    "src/frontend/dist/assets/index-D6jvqwd_.js",
    "src/frontend/dist/assets/index-CMMxxoQ-.css"
]

def calculate_sha256(filepath: str) -> str:
    full_path = os.path.join(project_root, filepath)
    if not os.path.exists(full_path):
        return "NOT_FOUND"
    sha256 = hashlib.sha256()
    with open(full_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def generate_checksums():
    checksum_lines = []
    print("Generating checksums.txt...")
    for rel_path in files_to_hash:
        sha = calculate_sha256(rel_path)
        if sha != "NOT_FOUND":
            checksum_lines.append(f"{sha}  {rel_path.replace('/', '\\')}")
            print(f"  {rel_path}: {sha}")
    
    with open(os.path.join(project_root, "checksums.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(checksum_lines) + "\n")
    print("checksums.txt written successfully.")

def generate_sbom():
    print("Generating SBOM.json...")
    sbom = {
        "sbomVersion": "1.0",
        "component": {
            "name": "ai-runtime-manager",
            "version": "1.0.0",
            "description": "Enterprise-grade local AI orchestration platform for Windows",
            "license": "MIT",
            "dependencies": [
                {"name": "fastapi", "version": "0.139.0", "license": "MIT", "purpose": "Web framework for local API gateway"},
                {"name": "uvicorn", "version": "0.50.0", "license": "BSD-3-Clause", "purpose": "ASGI web server"},
                {"name": "pywin32", "version": "312", "license": "PSF", "purpose": "Windows Native API integrations"},
                {"name": "psutil", "version": "7.2.2", "license": "BSD-3-Clause", "purpose": "Process management and hardware metrics"},
                {"name": "pyyaml", "version": "6.0.3", "license": "MIT", "purpose": "YAML configuration synthesis"},
                {"name": "pydantic", "version": "2.13.4", "license": "MIT", "purpose": "Data validation and settings management"},
                {"name": "react", "version": "19.2.7", "license": "MIT", "purpose": "Frontend UI component framework"},
                {"name": "react-dom", "version": "19.2.7", "license": "MIT", "purpose": "Frontend DOM bindings"},
                {"name": "lucide-react", "version": "1.23.0", "license": "ISC", "purpose": "UI Vector icons library"},
                {"name": "vite", "version": "8.1.3", "license": "MIT", "purpose": "Frontend build tooling"},
                {"name": "typescript", "version": "6.0.3", "license": "Apache-2.0", "purpose": "Frontend strict typing"},
                {"name": "pytest", "version": "9.1.1", "license": "MIT", "purpose": "Unit testing framework"},
                {"name": "httpx", "version": "0.28.1", "license": "BSD-3-Clause", "purpose": "HTTP client for validation and tests"}
            ]
        }
    }
    with open(os.path.join(project_root, "SBOM.json"), "w", encoding="utf-8") as f:
        json.dump(sbom, f, indent=2)
    print("SBOM.json written successfully.")

if __name__ == "__main__":
    generate_checksums()
    generate_sbom()
