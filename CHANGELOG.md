# Changelog

## v1.0.1

### Added

- Four download modes:
  - Audio
  - Video
  - Audio Playlist
  - Video Playlist
- Custom PNG icons for each download mode
- Bundled FFmpeg and FFprobe support for packaged releases
- Bundled yt-dlp support for packaged releases
- Organized download folders
- In-app progress panel
- Cleaner footer version display
- No-terminal PyInstaller build support
- Custom app icon support for packaged EXE
- Playlist skip handling for broken/unavailable items
- Protection against accidental full playlist downloads when using single Audio or Video mode
- GitHub Releases app updater
- Tool updater support for yt-dlp / FFmpeg / FFprobe
- Windows installer build using Inno Setup
- MIT License file

### Changed

- Reworked layout from old three-option design to 2x2 download mode layout
- Changed playlist downloads to separate playlist folders named after playlist title
- Changed normal downloads to save into Audio or Video folders
- Updated app version to v1.0.1
- Removed old requirement for normal users to manually install FFmpeg
- Updated README for installer-based release flow

### Fixed

- Fixed app launch issues caused by Flet image argument changes
- Fixed footer showing local FFmpeg directory instead of version text
- Fixed duplicate downloads between playlist folders and single-download folders
- Fixed taskbar/window icon for packaged builds
- Fixed terminal window requirement for packaged app builds

### Known Issue

- Windows taskbar right-click menu may still show `Flet description` on some systems.
  - This is cosmetic only.
  - Planned for v1.0.2.

## Planned for v1.0.2

- Polish Windows taskbar right-click metadata
- Further UI polish
- More robust updater status messages
- Optional updated user manual
