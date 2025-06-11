# Product Context

## Problem Statement
QLab users face significant challenges in selecting SSDs that guarantee stable and high-performance video playback, particularly with demanding 4K ProRes HQ content, multiple streams, and frame blending. Existing benchmarks often fail to simulate real-world QLab I/O patterns, leading to unexpected performance issues like dropped frames, stuttering, and thermal throttling during long shows. There is a critical need for a specialized tool that can accurately assess SSD suitability for these specific, high-demand scenarios, including long-term stability and latency for parallel stream access.

## User Experience Goals
- **Clarity:** Provide clear, actionable insights into an SSD's suitability for QLab's specific video playback requirements, including long-term stability, thermal performance, and latency for parallel streams.
- **Simplicity:** The testing process should be straightforward to execute, even for users without extensive technical knowledge of disk benchmarking, featuring intelligent disk detection, guided test selection, and a focus on offline installation.
- **Relevance:** The benchmark results should directly correlate with QLab's performance characteristics, particularly for 4K ProRes HQ playback with frame blending, thermal behavior during extended use, and cue response times.
- **Efficiency:** The testing tool should offer tiered test durations (Quick, Standard, Extended, Ultimate) to match user needs, providing results in a timely manner while allowing for comprehensive analysis.
- **Visual Appeal:** The command-line interface should be colorful, easy to read, and provide live monitoring with progress indicators and estimated completion times, enhancing the user experience.

## Target Audience
QLab users, show designers, video technicians, and anyone needing to select high-performance SSDs for live video playback applications on macOS.

## Key Use Cases
- **Pre-purchase evaluation:** Users can test potential SSDs before committing to a purchase.
- **System optimization:** Users can verify the performance of existing SSDs in their QLab setups.
- **Troubleshooting:** Identify if disk I/O is a bottleneck in a struggling QLab show.

## Success Metrics
- The tool accurately predicts an SSD's ability to handle 8 streams of 4K ProRes HQ with frame blending, including long-term stability and thermal performance.
- Users can easily interpret the comprehensive results, including QLab suitability ratings (✅/⚠️/❌) and specific recommendations, to make informed decisions about SSD selection.
- The tool is widely adopted and recommended within the QLab community for its accuracy, ease of use, and relevance to professional video playback workflows.
- The tool successfully operates in an offline environment, requiring no internet connection after initial setup.
