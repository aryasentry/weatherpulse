#!/usr/bin/env python3
"""Build the portable source/data/UI ZIP without virtualenvs or runtime downloads."""
import argparse
from datetime import datetime, timezone
import fnmatch
import hashlib
import os
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "Weather_Data_Analysis"
EXCLUDED_DIRS = {".runtime", ".ui-backups", ".venv", "node_modules", ".next", ".git", "dist", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".cache"}
EXCLUDED_FILES = {".DS_Store", "Thumbs.db", "RELEASE_SHA256SUMS.txt"}
EXCLUDED_PATTERNS = ("*.pyc", "*.pyo", "*.log", "*.pid", "*.tmp", "*.zip", "*~")
PRESERVED_PROOF = {"data/processed/hadoop-job.log"}
REQUIRED = ("README.md", "setup.py", "run.py", "requirements.txt", "Start-Windows.bat", "Start-Mac.command", "frontend/out/index.html", "data/processed/weather.parquet", "data/processed/manifest.json")


def release_files(root):
    for directory, dirs, files in os.walk(root):
        current = Path(directory)
        dirs[:] = sorted(name for name in dirs if name not in EXCLUDED_DIRS and not (current / name).is_symlink() and (current / name).relative_to(root).as_posix() != "frontend/design")
        for name in sorted(files):
            path = current / name
            proof = path.relative_to(root).as_posix() in PRESERVED_PROOF
            if path.is_symlink() or name in EXCLUDED_FILES or (not proof and any(fnmatch.fnmatch(name, pattern) for pattern in EXCLUDED_PATTERNS)):
                continue
            yield path


def digest_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def package(root, output, overwrite=False):
    missing = [name for name in REQUIRED if not (root / name).is_file()]
    if missing:
        raise RuntimeError("Missing release files: " + ", ".join(missing))
    files = list(release_files(root))
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        if not overwrite:
            raise RuntimeError(f"Archive already exists: {output}. Choose --output or use --overwrite to preserve it as a dated backup before rebuilding.")
        suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        output.replace(output.with_name(f"{output.stem}.backup-{suffix}{output.suffix}"))
    temporary = output.with_suffix(output.suffix + ".tmp")
    checksums = []
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path in files:
                relative = path.relative_to(root).as_posix()
                # Hash exactly the bytes that enter the archive, even if another
                # process regenerates a data artifact while the release builds.
                blob = path.read_bytes()
                info = zipfile.ZipInfo.from_file(path, f"{PREFIX}/{relative}")
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, blob, compresslevel=6)
                checksums.append(f"{hashlib.sha256(blob).hexdigest()}  {relative}\n")
            archive.writestr(f"{PREFIX}/RELEASE_SHA256SUMS.txt", "".join(checksums))
        with zipfile.ZipFile(temporary) as archive:
            bad = archive.testzip()
            if bad:
                raise RuntimeError(f"Archive integrity check failed: {bad}")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    sha = digest_file(output)
    sidecar = output.with_suffix(output.suffix + ".sha256")
    sidecar.write_text(f"{sha}  {output.name}\n", encoding="utf-8")
    print(f"Release: {output}\nFiles: {len(files)} plus internal SHA256 manifest\nSize: {output.stat().st_size:,} bytes\nSHA256: {sha}\nChecksum: {sidecar}")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "Weather_Data_Analysis_Windows_Mac_v3.zip")
    parser.add_argument("--overwrite", action="store_true", help="Preserve an existing output as a dated backup before rebuilding")
    args = parser.parse_args()
    try:
        package(ROOT, args.output.resolve(), args.overwrite)
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        print(f"Packaging failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
