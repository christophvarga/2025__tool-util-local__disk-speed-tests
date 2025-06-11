# Active Context

## Current Focus
The current focus is on refining the project plan and updating the Memory Bank to fully incorporate the detailed requirements for a comprehensive QLab SSD testing tool. This includes integrating multi-tier testing, intelligent disk detection, live monitoring, and advanced analysis capabilities.

## Key Decisions Made
- The project will be a stand-alone Python script, adhering strictly to Python standard library for "no dependencies" beyond `fio`.
- `fio` will remain the core benchmarking utility.
- The target OS is macOS, with a strong emphasis on offline installation and operation.
- The tool will feature four distinct test modes: Quick, Standard QLab, Extended Stress (with thermal analysis), and Ultimate Endurance.
- Intelligent disk detection and selection will be implemented.
- Live monitoring with progress tracking, ETA, and real-time bandwidth display will be provided.
- Results will include QLab-specific suitability analysis (4K stream count, cue response time) and professional recommendations.
- Output will be a colorful CLI report and a JSON export with automatic naming.
- Latency analysis for 8 parallel 4K ProRes HQ streams is a primary performance metric.

## Open Questions / Areas for Further Research
- **`fio` parameters for QLab simulation:** Precisely define the `fio` parameters (block size, I/O engine, `iodepth`, `numjobs`, etc.) for each of the four test tiers to accurately simulate QLab's 4K ProRes HQ playback, including long-term and thermal stress. This requires detailed research into ProRes HQ data rates and QLab's I/O patterns under various loads. (Initial research completed, parameters defined in `techContext.md`).
- **Thermal Monitoring Integration:** `smartctl` appears to be the most viable option for reading SSD temperature data. This will require providing clear, offline-friendly instructions for its installation (similar to `fio`). Further investigation into parsing `smartctl` output for temperature is needed.
- **Offline `fio` Installation Strategy:** Develop robust, user-friendly instructions for offline `fio` installation on macOS, considering scenarios where Homebrew might not be pre-installed or internet access is limited. This might involve providing direct download links for `fio` binaries or a script to download Homebrew components.
- **Intelligent Disk Detection Implementation:** `system_profiler SPStorageDataType` provides comprehensive and suitable information for reliably detecting and differentiating SSDs from HDDs, identifying mount points, and checking write permissions. Parsing its output will be key.
- **CLI Colorization and Live Updates:** Plan the implementation of ANSI escape codes for a visually appealing and dynamic CLI, ensuring compatibility across common macOS terminal emulators.

## Next Steps
1. Complete the update of all core Memory Bank files to reflect the refined project plan.
2. Begin detailed research into `fio` parameters for each test tier and ProRes HQ data rates.
3. Investigate macOS system commands for disk detection and thermal monitoring.
4. Outline the modular structure of the main Python script and start drafting core functions.
