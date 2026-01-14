from __future__ import annotations

from pathlib import Path


def process_files(directory: Path, pattern: str = "**/*") -> list[Path]:
    files = []

    for file_path in directory.glob(pattern):
        if file_path.is_file():
            files.append(file_path)
            print(f"Found: {file_path}")

    return files


def main():
    test_dir = Path(__file__).parent
    files = process_files(test_dir)

    print(f"\nTotal files found: {len(files)}")

    for file_path in files:
        size = file_path.stat().st_size
        print(f"  {file_path.name}: {size} bytes")


if __name__ == "__main__":
    main()
