# Vibe Downloader Pro

Vibe Downloader Pro is a Windows desktop downloader for audio, video, audio playlists, and video playlists.

Created by Anders M. Johansen / @MisguidedSage  
Released under the MIT License.

## Current Version

v1.0.2

## Features

- Download single audio files
- Download single video files
- Download audio playlists
- Download video playlists
- Separate mode-specific queues:
  - Audio Queue
  - Video Queue
  - Audio Playlist Queue
  - Video Playlist Queue
- Queue cache recovery after app restart
- Failed queue jobs stay saved for retry
- Completed queue jobs are removed automatically
- Audio quality selector
- Audio format selector
- Video quality selector
- Video format selector
- Queue Speed selector with Normal and Gentle / Fewer Bot Checks modes
- Automatic YouTube browser-cookie retry for sign-in / bot-check errors when possible
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
    ├── Video Playlist
    │   └── Playlist Name
    └── _app_cache
        └── queue_cache.json

The `_app_cache` folder stores queue recovery data. It is used by the app so queued jobs can survive an app restart.

## User Installation

For normal users:

1. Go to the GitHub Releases section.
2. Download `VibeDownloaderProSetup-v1.0.2.exe`.
3. Run the installer.
4. Launch Vibe Downloader Pro.
5. Paste one supported URL or multiple supported URLs.
6. Choose your audio/video quality and format settings.
7. Click `Download Now` on the mode you want, or click `Add To Queue`.
8. For queued downloads, use the matching `Download Queue` button.

No terminal setup is required for the packaged release.

## Queue System

v1.0.2 includes four separate queues:

- Audio Queue
- Video Queue
- Audio Playlist Queue
- Video Playlist Queue

Each queue remembers the selected quality and format settings from when the URL was added.

Completed queued jobs are removed automatically. Failed jobs stay saved and are marked for retry.

## YouTube Bot-Check / Sign-In Handling

Some YouTube downloads may trigger sign-in or bot-check verification.

When possible, Vibe Downloader Pro will automatically retry using signed-in browser cookies from supported browsers. This is handled behind the scenes and does not require a separate YouTube access mode.

The `Gentle / Fewer Bot Checks` queue speed option adds slower pacing between queued jobs.

## Updates

Vibe Downloader Pro includes:

- App update checking through GitHub Releases
- Tool update checking for download tools

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

    py "Vibe Downloader Pro v1.0.2.py"

Packaged release builds are created with PyInstaller and Inno Setup.

## Known Issues

- The progress bar may not visually update in real time when Vibe Downloader Pro is visible but not the active window.
  - Downloads continue normally.
  - Clicking back into the app usually refreshes the displayed progress.
- On some Windows systems, the taskbar right-click menu may still show `Flet description`.
  - This is cosmetic only and does not affect downloads, installation, updates, or app functionality.

## Notes

- Release builds bundle FFmpeg, FFprobe, and yt-dlp support.
- Build output should go in GitHub Releases, not regular source commits.
- Do not upload terminal logs, test folders, backup scripts, rollback backups, or local build junk.

## License

Released under the MIT License.
