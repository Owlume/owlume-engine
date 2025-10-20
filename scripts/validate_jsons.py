# scripts/validate_jsons.py
import json, os, sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(ROOT, "data")
SCHEMA_DIR = os.path.join(ROOT, "schema")

def validate_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            json.load(f)
        print(f"✓ {os.path.basename(path)} - valid JSON")
    except json.JSONDecodeError as e:
        print(f"✗ {os.path.basename(path)} - JSON error: {e}")
    except Exception as e:
        print(f"✗ {os.path.basename(path)} - cannot read: {e}")

def main():
    print("\nVALIDATING JSON PACKS...\n")
    data_files = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f.endswith(".json")]
    if not data_files:
        print("No JSON files found in /data")
        return
    for file in data_files:
        validate_json(file)
    print("\nValidation complete.\n")

if __name__ == "__main__":
    main()
