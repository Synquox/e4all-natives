# e4all native libraries

This repository builds the JNI library used by e4all and publishes versioned desktop releases.

Desktop releases use tags named `natives-<version>`. Each release contains the six desktop library files, `manifest-desktop.json`, and `desktop-hashes.properties`. The Android task uses its own `natives-android-<version>` tags and is not handled by this workflow.

The mod keeps the existing e4mc CDN loader for x64. ARM64 clients use the GitHub release assets from this repository. The x64 entries remain in the release manifest to keep the desktop release format consistent.

The workflow builds from the pinned `vgskye/iroh-java` source revision in the `IROH_JAVA_REF` repository variable. The current pin is the source revision matching the native filenames used by `iroh-java` 0.1.2.

To publish a desktop release, push a `natives-<version>` tag. GitHub Actions builds all six targets and creates the release with its manifest and hash list.
