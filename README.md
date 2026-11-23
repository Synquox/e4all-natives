# e4all native libraries

This repository builds and publishes the native library used by e4all. Desktop releases use tags named `natives-<version>` and include all six platform files, `manifest-desktop.json`, and `desktop-hashes.properties`.

x64 clients continue to use the e4mc CDN through the existing `iroh-java` loader. ARM64 clients download their native from this repository's GitHub Releases.

The workflow builds the `vgskye/iroh-java` Rust source at the commit set in the `IROH_JAVA_REF` Actions variable. Push a `natives-<version>` tag to build and publish a desktop release. Android uses separate `natives-android-<version>` releases.
