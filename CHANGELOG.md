# Changelog

## v1.0.2

### Added

- Batch downloading support with mode-specific queues:
  - Audio Queue
  - Video Queue
  - Audio Playlist Queue
  - Video Playlist Queue
- Persistent queue cache stored in the user's Downloads folder:
  - `Downloads\Vibe Downloader Pro\_app_cache\queue_cache.json`
- Separate audio quality selector:
  - Best Quality
  - 320 kbps
  - 256 kbps
  - 192 kbps
  - 128 kbps
- Separate audio format selector:
  - MP3
  - M4A
  - OPUS
  - WAV
  - FLAC
- Separate video quality selector:
  - Best Quality
  - 2160p / 4K
  - 1440p / 2K
  - 1080p
  - 720p
  - 480p
  - 360p
- Separate video format selector:
  - Best / Auto
  - MP4
  - WEBM
  - MKV
- Queue Speed selector:
  - Normal
  - Gentle / Fewer Bot Checks
- Automatic retry support for YouTube sign-in / bot-check errors using available signed-in browser cookies.
- Failed queue jobs remain saved for retry instead of disappearing.
- Queue recovery after app restart.
- Scroll support for the larger desktop layout.

### Changed

- Audio Quality now defaults to Best Quality instead of 192 kbps.
- Reworked the workflow so each mode card has:
  - Download Now
  - Add To Queue
- Replaced the single shared queue with separate queues for each download mode.
- Queue jobs remember the selected quality and format settings from the moment they are added.
- Completed queued jobs are removed after successful download.
- Failed queued jobs stay visible and are marked as failed.
- Cleaned YouTube bot-check error spam into shorter user-facing messages.
- Improved progress update handling internally.
- Cleaned supported-sites list formatting.

### Fixed

- Fixed confusing single-queue behavior by splitting queues by download mode.
- Fixed queue loss on app restart by adding persistent queue cache.
- Fixed weird supported-sites bullet characters.
- Fixed audio default quality behavior.
- Fixed versioned v1.0.2 app metadata references.
- Fixed installer source and output paths for v1.0.2.
- Fixed Windows numeric file/product version metadata for v1.0.2 builds.

### Known Issues

- The progress bar may not visually update in real time when Vibe Downloader Pro is visible but not the active window.
  - Downloads continue normally.
  - Clicking back into the app usually refreshes the displayed progress.
- Windows taskbar right-click menu may still show `Flet description` on some systems.
  - This is cosmetic only.

## v1.0.1

- Previous public GitHub release.
