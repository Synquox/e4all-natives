#!/usr/bin/env python3
"""Extract Android native files from an existing e4all jar and publish them."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

FILES = (
    "libc++_shared.so",
    "libcxxpreload.so",
    "libiroh_java.so",
    "libnetty_quiche.so",
)
ABI = "arm64-v8a"
KEY = "android-" + ABI


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jar", type=Path, help="existing e4all -android jar containing the original files")
    parser.add_argument("--version", default=os.environ.get("NATIVE_VERSION", "1"))
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", "Synquox/e4all-natives"))
    parser.add_argument("--output", type=Path, default=Path("dist/android"))
    parser.add_argument("--no-publish", action="store_true", help="prepare assets and manifest without calling gh")
    args = parser.parse_args()
    version = args.version.strip()
    if not version or any(c not in "0123456789.-" for c in version):
        raise SystemExit("Version must contain only digits, dots, or hyphens")
    if not args.jar.is_file():
        raise SystemExit(f"Jar not found: {args.jar}")

    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    tag = "natives-android-" + version
    entries = []
    hashes = ["# SHA-256 hashes for the e4all Android native release."]
    with zipfile.ZipFile(args.jar) as jar:
        for native in FILES:
            source = f"assets/e4all/natives/android-aarch64/{native}"
            try:
                data = jar.read(source)
            except KeyError:
                raise SystemExit(f"Android jar is missing {source}")
            suffix = "" if native == "libnetty_quiche.so" else "-" + native[:-3].replace("+", "x")
            asset = f"e4all-native-{version}-{KEY}{suffix}.so"
            target = out / asset
            target.write_bytes(data)
            digest = hashlib.sha256(data).hexdigest()
            url = f"https://github.com/{args.repository}/releases/download/{tag}/{asset}"
            entries.append({"name": native, "urls": [url], "sha256": digest, "size": len(data)})
            hashes.append(f"android.{KEY}.{native}={digest}")

    manifest = {"nativeVersion": version, "platforms": {KEY: {"files": entries}}}
    manifest_path = out / "manifest-android.json"
    hashes_path = out / "android-hashes.properties"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    hashes_path.write_text("\n".join(hashes) + "\n", encoding="utf-8")
    print(f"Prepared Android assets in {out}")
    print(f"Manifest: {manifest_path}")

    if args.no_publish:
        return
    assets = [str(out / f"e4all-native-{version}-{KEY}{('-' + n[:-3].replace('+', 'x')) if n != 'libnetty_quiche.so' else ''}.so") for n in FILES]
    assets.extend([str(manifest_path), str(hashes_path)])
    exists = subprocess.run(["gh", "release", "view", tag, "--repo", args.repository], capture_output=True, text=True)
    if exists.returncode != 0:
        subprocess.run(["gh", "release", "create", tag, "--repo", args.repository,
                        "--title", "Android natives " + version,
                        "--notes", "Android native libraries extracted unchanged from the existing e4all Android jar."], check=True)
    subprocess.run(["gh", "release", "upload", tag, *assets, "--repo", args.repository, "--clobber"], check=True)
    print(f"Published {tag} to {args.repository}")


if __name__ == "__main__":
    main()
