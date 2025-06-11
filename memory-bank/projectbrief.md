# Project Brief

## Project Name
Stand-alone Python SSD Speed Test for macOS

## Project Goal
To develop a stand-alone Python application for testing SSD speeds on macOS using `fio`, specifically tailored to identify suitable SSDs for QLab shows requiring high-performance video playback.

## Key Objectives
- Develop a stand-alone Python application for macOS to perform comprehensive SSD speed tests using `fio`.
- Implement intelligent disk detection and selection.
- Provide multi-tier testing modes (Quick, Standard QLab, Extended Stress, Ultimate Endurance) including thermal analysis and long-term stability.
- Focus on latency analysis for 8 parallel 4K ProRes HQ video streams with frame blending.
- Ensure compatibility with a clean macOS environment with a strong focus on offline installation.
- Present live monitoring of test progress and results.
- Generate intelligent analysis, QLab suitability ratings, and professional reports with JSON export.

## Scope
- Development of the Python script to orchestrate `fio` tests and manage the testing workflow.
- Intelligent detection and selection of target SSDs.
- Creation of `fio` job files tailored for various test durations and QLab-specific scenarios (including thermal and long-term tests).
- Real-time monitoring of performance metrics (bandwidth, IOPS, latency) and estimated completion time.
- Comprehensive analysis of `fio` output, including QLab suitability assessment (stream count, cue response time) and production recommendations.
- Implementation of a colorful and user-friendly command-line interface.
- JSON export of detailed results with automatic file naming.
- Provision of clear instructions for `fio` installation and ensuring offline functionality.

## Out of Scope
- Development of `fio` itself.
- General-purpose disk benchmarking unrelated to QLab's specific needs.
- Cross-platform compatibility (focus exclusively on macOS).
