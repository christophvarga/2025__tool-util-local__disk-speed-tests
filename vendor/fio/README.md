# Vendored FIO for Offline Use

Version 1.0 – 04.09.2025

Place prebuilt FIO binaries here to enable fully offline operation on macOS.

Layout:
- macOS Apple Silicon (primary):
  - vendor/fio/macos/arm64/fio         (executable)
  - optional: vendor/fio/macos/arm64/fio-noshm (if you have a no-SHM build)
- macOS Intel (optional fallback for dev/test):
  - vendor/fio/macos/x86_64/fio

Notes:
- Ensure the file has executable permissions: chmod +x vendor/fio/macos/arm64/fio
- The app prefers vendored FIO first; Homebrew/system PATH are fallbacks.
- Environment: FIO_DISABLE_SHM=1 is set by the bridge and runner.

Licensing:
- FIO is licensed under GPLv2. If you distribute a FIO binary with this repository, include the GPLv2 license text here as vendor/fio/LICENSE and provide a reference to the source you used to build it (e.g., https://github.com/axboe/fio).

