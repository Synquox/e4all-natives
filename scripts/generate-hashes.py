#!/usr/bin/env python3
"""Write the desktop release manifest and hash list."""
import hashlib
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

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


def hash_url(url):
    request = Request(url, headers={"User-Agent": "e4all-native-release"})
    digest = hashlib.sha256()
    size = 0
    with urlopen(request, timeout=30) as response:
        if not response.geturl().startswith("https://"):
            raise SystemExit(f"Refusing non-HTTPS URL: {response.geturl()}")
        while True:
            block = response.read(65536)
            if not block:
                break
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size


def local_entry(dist: Path, name: str):
    path = dist / name
    if not path.is_file():
        raise SystemExit(f"Missing native artifact: {path}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    size = path.stat().st_size
    url = f"https://github.com/{REPOSITORY}/releases/download/natives-{VERSION}/{name}"
    return {
        "name": name,
        "urls": [url],
        "sha256": digest,
        "size": size,
    }


if not VERSION:
    raise SystemExit("Set NATIVE_VERSION or run on a natives-<version> tag")

dist = Path("dist")
dist.mkdir(exist_ok=True)
manifest = {"nativeVersion": VERSION}
hashes = ["# SHA-256 hashes for the e4all desktop native release."]
for key, (os_name, arch, extension) in ARTIFACTS.items():
    name = f"e4all-native-{VERSION}-{os_name}-{arch}.{extension}"
    if key == "windows-aarch64":
        quiche_name = f"e4all-quiche-{VERSION}-windows-aarch64.dll"
        iroh_entry = local_entry(dist, name)
        quiche_entry = local_entry(dist, quiche_name)
        manifest[key] = {"files": [iroh_entry, quiche_entry]}
        hashes.append(f"desktop.{key}.{name}={iroh_entry['sha256']}")
        hashes.append(f"desktop.{key}.{quiche_name}={quiche_entry['sha256']}")
        continue

    path = dist / name
    if not path.is_file():
        raise SystemExit(f"Missing native artifact: {path}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    size = path.stat().st_size
    if key in E4MC_X64_FILENAMES:
        urls = [f"https://natives.e4mc.link/{E4MC_X64_FILENAMES[key]}"]
        digest, size = hash_url(urls[0])
    else:
        urls = [f"https://github.com/{REPOSITORY}/releases/download/natives-{VERSION}/{name}"]
    manifest[key] = {
        "urls": urls,
        "sha256": digest,
        "size": size,
    }
    hashes.append(f"desktop.{key}={digest}")

(dist / "manifest-desktop.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
(dist / "desktop-hashes.properties").write_text("\n".join(hashes) + "\n", encoding="utf-8")
