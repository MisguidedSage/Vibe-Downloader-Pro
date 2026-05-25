# Vibe Downloader Pro

Vibe Downloader Pro is a Windows desktop downloader for audio, video, audio playlists, and video playlists.

Created by Anders M. Johansen / @MisguidedSage  
Released under the MIT License.

## Current Version

v1.0.1

## Features

- Download single audio files
- Download single video files
- Download audio playlists
- Download video playlists
- Organized download folders
- In-app download progress display
- Playlist skip handling for unavailable items
- Bundled FFmpeg and FFprobe for packaged releases
- Bundled yt-dlp support for packaged releases
- In-app tool updater for yt-dlp / FFmpeg / FFprobe support
- GitHub Releases app updater support
- Windows installer
- No manual Python install required for normal users
- No manual FFmpeg install required for normal users
- Custom app icon
- No-terminal Windows app build

## Download Folder Structure

Files save inside:

    Downloads\Vibe Downloader Pro

Folder layout:

    Vibe Downloader Pro
    ├── Audio
    ├── Video
    ├── Audio Playlist
    │   └── Playlist Name
    └── Video Playlist
        └── Playlist Name

## User Installation

For normal users:

1. Go to the GitHub Releases section.
2. Download `VibeDownloaderProSetup-v1.0.1.exe`.
3. Run the installer.
4. Launch Vibe Downloader Pro.
5. Paste a supported URL.
6. Choose Audio, Video, Audio Playlist, or Video Playlist.
7. Click Download.

No terminal setup is required for the packaged release.

## Updates

Vibe Downloader Pro includes:

- App update checking through GitHub Releases
- Tool update checking for download tools

Future app versions can be distributed through GitHub Releases.

## Supported Sites

Vibe Downloader Pro uses yt-dlp, which supports many sites, including:

- YouTube
- Vimeo
- TikTok
- Instagram
- Dailymotion
- Twitch
- Reddit
- Twitter/X
- Facebook
- SoundCloud
- 1000+ more supported sites

## Developer Setup

For developers who want to modify the source:

    pip install -r requirements.txt

Run from source:

    py "Vibe Downloader Pro v1.0.1.py"

Packaged release builds are created with PyInstaller and Inno Setup.

## Known Issue

On some Windows systems, the taskbar right-click menu may still show `Flet description`.

This is cosmetic only. It does not affect downloads, installation, updates, or app functionality.

Planned for v1.0.2:

- Polish Windows taskbar right-click metadata

## Notes

- Release builds bundle FFmpeg, FFprobe, and yt-dlp support.
- Build output should go in GitHub Releases, not regular source commits.
- Do not upload terminal logs, test folders, backup scripts, rollback backups, or local build junk.

## License

Released under the MIT License.
