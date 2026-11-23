#!/usr/bin/env python3
"""Write the desktop release manifest and hash list."""
import hashlib
import json
import os
from pathlib import Path

VERSION = os.environ.get("NATIVE_VERSION") or os.environ.get("GITHUB_REF_NAME", "").removeprefix("natives-")
REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "Synquox/e4all-natives")
ARTIFACTS = {
    "windows-x64": ("windows", "x64", "dll"),
    "windows-aarch64": ("windows", "aarch64", "dll"),
    "linux-x64": ("linux", "x64", "so"),
    "linux-aarch64": ("linux", "aarch64", "so"),
    "macos-x64": ("macos", "x64", "dylib"),
    "macos-aarch64": ("macos", "aarch64", "dylib"),
}
# Filenames served by the existing e4mc CDN for x64 clients.
E4MC_X64_FILENAMES = {
    "windows-x64": "iroh_java_windows_x86_64_b296210.dll",
    "linux-x64": "libiroh_java_linux_x86_64_b296210.so",
    "macos-x64": "libiroh_java_osx_x86_64_b296210.dylib",
}

if not VERSION:
    raise SystemExit("Set NATIVE_VERSION or run on a natives-<version> tag")

dist = Path("dist")
dist.mkdir(exist_ok=True)
manifest = {"nativeVersion": VERSION}
hashes = ["# SHA-256 hashes for the e4all desktop native release."]
for key, (os_name, arch, extension) in ARTIFACTS.items():
    name = f"e4all-native-{VERSION}-{os_name}-{arch}.{extension}"
    path = dist / name
    if not path.is_file():
        raise SystemExit(f"Missing native artifact: {path}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    urls = []
    if key in E4MC_X64_FILENAMES:
        urls.append(f"https://natives.e4mc.link/{E4MC_X64_FILENAMES[key]}")
    urls.append(f"https://github.com/{REPOSITORY}/releases/download/natives-{VERSION}/{name}")
    manifest[key] = {
        "urls": urls,
        "sha256": digest,
        "size": path.stat().st_size,
    }
    hashes.append(f"desktop.{key}={digest}")

(dist / "manifest-desktop.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
(dist / "desktop-hashes.properties").write_text("\n".join(hashes) + "\n", encoding="utf-8")
