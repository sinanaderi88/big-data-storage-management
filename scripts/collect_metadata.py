from pathlib import Path
from datetime import datetime
import csv

ROOT = Path("/home/sina/bigdata-lab/storage_lab/bronze")
OUTPUT = Path("/home/sina/bigdata-lab/storage_lab/metadata/metadata_inventory.csv")


def get_file_type(file_path):
    suffix = file_path.suffix.lower()

    if suffix:
        return suffix.lstrip(".")

    return "unknown"


def collect_metadata():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for path in ROOT.rglob("*"):

        # File
        if path.is_file():

            stat = path.stat()
            modified = datetime.fromtimestamp(stat.st_mtime)

            rows.append({
                "ParentPath": str(path.parent),
                "FullPath": str(path),
                "Type": get_file_type(path),
                "FileSizeBytes": stat.st_size,
                "ModificationDate": modified.strftime("%Y-%m-%d"),
                "ModificationTime": modified.strftime("%H:%M:%S")
            })

        # Empty directory
        elif path.is_dir():

            try:
                is_empty = not any(path.iterdir())
            except PermissionError:
                is_empty = False

            if is_empty:
                rows.append({
                    "ParentPath": str(path),
                    "FullPath": "",
                    "Type": "EMPTY_DIRECTORY",
                    "FileSizeBytes": 0,
                    "ModificationDate": "",
                    "ModificationTime": ""
                })

    with OUTPUT.open("w", newline="", encoding="utf-8") as f:

        fieldnames = [
            "ParentPath",
            "FullPath",
            "Type",
            "FileSizeBytes",
            "ModificationDate",
            "ModificationTime"
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(rows)

    print(f"Metadata collection completed.")
    print(f"Root       : {ROOT}")
    print(f"Output     : {OUTPUT}")
    print(f"Records    : {len(rows)}")


if __name__ == "__main__":
    collect_metadata()
