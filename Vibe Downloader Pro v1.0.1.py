import ctypes
import os
import re
import sys
import warnings
import threading
import time
import json
import subprocess
import shutil
import zipfile
import urllib.error
import urllib.request
from pathlib import Path

import flet as ft
import yt_dlp


APP_NAME = "Vibe Downloader Pro"
APP_VERSION = "1.0.1"
APP_ID = "InFiniteStudios.VibeDownloaderPro.v101"
APP_ICON_FILENAME = "VDL_PRO_ICO.ico"

GITHUB_OWNER = "MisguidedSage"
GITHUB_REPO = "Vibe-Downloader-Pro"
GITHUB_LATEST_RELEASE_API = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
UPDATE_INSTALLER_KEYWORDS = ["setup", "installer"]

YTDLP_EXE_DOWNLOAD_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
TOOL_BUNDLE_KEYWORDS = ["tools", "tool", "dependencies", "bin"]
TOOL_EXE_NAMES = ["yt-dlp.exe", "ffmpeg.exe", "ffprobe.exe"]

warnings.filterwarnings("ignore", category=DeprecationWarning)

ICON_FILES = {
    "Audio": "audio.png",
    "Video": "video.png",
    "Audio Playlist": "audio_playlist.png",
    "Video Playlist": "video_playlist.png",
}

SUPPORTED_PLATFORMS = [
    "YouTube",
    "Vimeo",
    "TikTok",
    "Instagram",
    "Dailymotion",
    "Twitch",
    "Reddit",
    "Twitter/X",
    "Facebook",
    "SoundCloud",
    "And 1000+ more sites",
]




def get_local_app_data_dir():
    local_app_data = os.environ.get("LOCALAPPDATA")

    if local_app_data:
        return Path(local_app_data)

    return Path.home() / "AppData" / "Local"


def get_user_tools_dir():
    return get_local_app_data_dir() / APP_NAME / "bin"


def get_updated_ffmpeg_location():
    bin_path = get_user_tools_dir()
    ffmpeg_path = bin_path / "ffmpeg.exe"
    ffprobe_path = bin_path / "ffprobe.exe"

    if ffmpeg_path.exists() and ffprobe_path.exists():
        os.environ["PATH"] = f"{bin_path}{os.pathsep}{os.environ.get('PATH', '')}"
        return str(bin_path)

    return None


def run_hidden_process(args, timeout=20):
    creationflags = 0

    if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
        creationflags = subprocess.CREATE_NO_WINDOW

    return subprocess.run(
        [str(item) for item in args],
        capture_output=True,
        text=True,
        timeout=timeout,
        creationflags=creationflags,
    )


def validate_tool(tool_path, args):
    if not Path(tool_path).exists():
        raise RuntimeError(f"Missing tool after download: {Path(tool_path).name}")

    result = run_hidden_process([tool_path] + list(args), timeout=20)

    if result.returncode != 0:
        error_text = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"{Path(tool_path).name} failed validation: {error_text[:120]}")

    return (result.stdout or result.stderr or "").strip()


def download_url_to_file(url, destination_path, progress_callback=None):
    destination_path = Path(destination_path)
    destination_path.parent.mkdir(parents=True, exist_ok=True)

    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}"},
    )

    with urllib.request.urlopen(request, timeout=90) as response:
        total_size = int(response.headers.get("Content-Length") or 0)
        downloaded_size = 0

        with open(destination_path, "wb") as output_file:
            while True:
                chunk = response.read(1024 * 256)

                if not chunk:
                    break

                output_file.write(chunk)
                downloaded_size += len(chunk)

                if progress_callback and total_size:
                    progress_callback(downloaded_size, total_size)

    return destination_path


def find_tools_bundle_asset(release_data):
    assets = release_data.get("assets") or []

    for asset in assets:
        name = asset.get("name") or ""
        download_url = asset.get("browser_download_url") or ""
        lowered_name = name.lower()

        if not lowered_name.endswith(".zip"):
            continue

        if not download_url:
            continue

        if any(keyword in lowered_name for keyword in TOOL_BUNDLE_KEYWORDS):
            return asset

    return None


def find_file_recursively(folder, filename):
    folder = Path(folder)

    for item in folder.rglob(filename):
        if item.is_file():
            return item

    return None


def normalize_version(version_text):
    version_text = str(version_text or "").strip().lstrip("vV")
    numbers = re.findall(r"\d+", version_text)

    if not numbers:
        return (0, 0, 0)

    version_parts = [int(part) for part in numbers[:3]]

    while len(version_parts) < 3:
        version_parts.append(0)

    return tuple(version_parts)


def is_newer_version(latest_version, current_version):
    return normalize_version(latest_version) > normalize_version(current_version)


def github_request_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{APP_NAME}/{APP_VERSION}",
        },
    )

    with urllib.request.urlopen(request, timeout=12) as response:
        raw = response.read().decode("utf-8")

    return json.loads(raw)


def find_update_asset(release_data):
    assets = release_data.get("assets") or []
    preferred_assets = []
    fallback_assets = []

    for asset in assets:
        name = asset.get("name") or ""
        download_url = asset.get("browser_download_url") or ""

        if not name.lower().endswith(".exe"):
            continue

        if not download_url:
            continue

        lowered_name = name.lower()

        if any(keyword in lowered_name for keyword in UPDATE_INSTALLER_KEYWORDS):
            preferred_assets.append(asset)
        else:
            fallback_assets.append(asset)

    if preferred_assets:
        return preferred_assets[0]

    if fallback_assets:
        return fallback_assets[0]

    return None


def configure_windows_app_identity():
    if sys.platform != "win32":
        return

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass

def app_base_paths():
    paths = []

    if getattr(sys, "frozen", False):
        paths.append(Path(sys.executable).resolve().parent)

    if hasattr(sys, "_MEIPASS"):
        paths.append(Path(sys._MEIPASS).resolve())

    paths.append(Path(__file__).resolve().parent)

    unique_paths = []
    for path in paths:
        if path not in unique_paths:
            unique_paths.append(path)

    return unique_paths


def find_resource(filename):
    for base_path in app_base_paths():
        candidate = base_path / filename
        if candidate.exists():
            return candidate

    return None


def get_app_icon_path():
    return find_resource(APP_ICON_FILENAME)


def get_ffmpeg_location():
    for base_path in app_base_paths():
        bin_path = base_path / "bin"
        ffmpeg_path = bin_path / "ffmpeg.exe"
        ffprobe_path = bin_path / "ffprobe.exe"

        if ffmpeg_path.exists() and ffprobe_path.exists():
            os.environ["PATH"] = f"{bin_path}{os.pathsep}{os.environ.get('PATH', '')}"
            return str(bin_path)

    return None


def get_format_string(selected_quality):
    if selected_quality == "1080":
        return "bestvideo[height<=1080]+bestaudio/best"
    if selected_quality == "720":
        return "bestvideo[height<=720]+bestaudio/best"
    if selected_quality == "worst":
        return "worst"

    return "bestvideo+bestaudio/best"


def strip_ansi(value):
    if value is None:
        return ""

    return re.sub(r"\x1b\[[0-9;]*m", "", str(value)).strip()


def safe_percent_from_hook(data):
    percent_text = strip_ansi(data.get("_percent_str"))

    if percent_text:
        match = re.search(r"(\d+(?:\.\d+)?)", percent_text)
        if match:
            percent_number = float(match.group(1))
            return max(0, min(percent_number / 100, 1)), f"{percent_number:.1f}%"

    downloaded = data.get("downloaded_bytes") or 0
    total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0

    if downloaded and total:
        progress_value = max(0, min(downloaded / total, 1))
        return progress_value, f"{progress_value * 100:.1f}%"

    return None, "Working..."


def main(page: ft.Page):
    page.title = APP_NAME
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 24
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    app_icon = get_app_icon_path()
    if app_icon:
        icon_path = str(app_icon)

        # Newer Flet window API
        try:
            page.window.icon = icon_path
        except Exception:
            pass

        # Older Flet window API fallback
        try:
            page.window_icon = icon_path
        except Exception:
            pass

    try:
        page.window.width = 760
        page.window.height = 920
    except Exception:
        page.window_width = 760
        page.window_height = 920

    icon_cache = {
        mode: find_resource(filename)
        for mode, filename in ICON_FILES.items()
    }

    download_log_entries = []
    warning_count = {"count": 0}
    download_in_progress = {"active": False}
    download_progress_state = {
        "is_playlist": False,
        "completed": 0,
        "total": 0,
        "current_index": 0,
    }
    smooth_progress_state = {
        "active": False,
        "target": 0.0,
        "displayed": 0.0,
        "detail": "Waiting...",
    }

    url_input = ft.TextField(
        label="Paste URL Here",
        hint_text="https://...",
        autofocus=True,
        width=620,
    )

    quality_dropdown = ft.Dropdown(
        label="Select Video Quality",
        width=300,
        options=[
            ft.dropdown.Option("best", text="Best Quality"),
            ft.dropdown.Option("1080", text="HD 1080p"),
            ft.dropdown.Option("720", text="Standard 720p"),
            ft.dropdown.Option("worst", text="Data Saver"),
        ],
        value="best",
    )

    progress_title = ft.Text(
        value="Download Progress",
        size=12,
        weight="bold",
        color="#90CAF9",
        text_align=ft.TextAlign.CENTER,
        width=620,
    )

    progress_bar = ft.ProgressBar(
        width=620,
        value=0,
        color="#64B5F6",
        bgcolor="#263238",
    )

    progress_percent_text = ft.Text(
        value="0%",
        size=12,
        color="#E3F2FD",
        text_align=ft.TextAlign.CENTER,
        width=620,
    )

    progress_detail_text = ft.Text(
        value="Waiting...",
        size=11,
        color="#B0BEC5",
        text_align=ft.TextAlign.CENTER,
        width=620,
    )

    progress_panel = ft.Container(
        visible=False,
        width=650,
        padding=14,
        border_radius=16,
        bgcolor="#171B20",
        content=ft.Column(
            [
                progress_title,
                progress_bar,
                progress_percent_text,
                progress_detail_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
        ),
    )

    status_text = ft.Text(
        value="Ready to vibe.",
        italic=True,
        color="#BDBDBD",
        text_align=ft.TextAlign.CENTER,
        width=620,
    )

    log_title = ft.Text(
        value="Skipped / Error Log",
        size=12,
        weight="bold",
        color="#FFCC80",
        visible=False,
        width=620,
    )

    log_text = ft.Text(
        value="",
        size=10,
        color="#FFCC80",
        selectable=True,
        visible=False,
        width=620,
    )

    log_panel = ft.Container(
        visible=False,
        width=650,
        padding=12,
        border_radius=14,
        bgcolor="#1C1712",
        content=ft.Column(
            [log_title, log_text],
            spacing=4,
        ),
    )

    def set_status(message, color="#BDBDBD"):
        status_text.value = message
        status_text.color = color
        page.update()

    def reset_log():
        download_log_entries.clear()
        warning_count["count"] = 0
        log_title.visible = False
        log_text.visible = False
        log_panel.visible = False
        log_text.value = ""

    def append_log(message, count_warning=True):
        cleaned = strip_ansi(message)

        if not cleaned:
            return

        if count_warning:
            warning_count["count"] += 1

        download_log_entries.append(cleaned)

        if len(download_log_entries) > 12:
            download_log_entries.pop(0)

        log_text.value = "\n".join(f"• {entry}" for entry in download_log_entries)
        log_title.visible = True
        log_text.visible = True
        log_panel.visible = True
        page.update()

    class AppLogger:
        def debug(self, msg):
            pass

        def warning(self, msg):
            # Hide non-fatal yt-dlp warnings from normal users.
            # Example: JavaScript runtime warning. Downloads can still work fine.
            pass

        def error(self, msg):
            cleaned = strip_ansi(msg)

            ignored_phrases = [
                "No supported JavaScript runtime could be found",
                "Only deno is enabled by default",
                "to use another runtime add",
                "YouTube extraction without a JS runtime",
            ]

            if any(phrase.lower() in cleaned.lower() for phrase in ignored_phrases):
                return

            if cleaned:
                append_log(f"Skipped/Error: {cleaned}", count_warning=True)

    def clamp_progress(value):
        try:
            value = float(value)
        except Exception:
            value = 0.0

        return max(0.0, min(value, 1.0))

    def set_progress_target(value, detail=None):
        smooth_progress_state["target"] = clamp_progress(value)

        if detail is not None:
            smooth_progress_state["detail"] = detail

    def start_progress_animator():
        smooth_progress_state["active"] = True
        smooth_progress_state["target"] = 0.0
        smooth_progress_state["displayed"] = 0.0
        smooth_progress_state["detail"] = "Starting..."

        def animator():
            dot_count = 0

            while (
                smooth_progress_state["active"]
                or smooth_progress_state["displayed"] < smooth_progress_state["target"] - 0.001
            ):
                target = smooth_progress_state["target"]
                displayed = smooth_progress_state["displayed"]

                if displayed < target:
                    step = max((target - displayed) * 0.14, 0.003)
                    displayed = min(displayed + step, target)
                    smooth_progress_state["displayed"] = displayed
                elif download_in_progress["active"] and target < 0.97:
                    # Gentle visual creep so users know the app is still alive
                    # while yt-dlp is extracting metadata or FFmpeg is processing.
                    creep_target = min(target + 0.035, 0.97)
                    step = max((creep_target - displayed) * 0.03, 0.0006)

                    if displayed < creep_target:
                        displayed = min(displayed + step, creep_target)
                        smooth_progress_state["displayed"] = displayed

                dots = "." * (dot_count % 4)
                dot_count += 1

                progress_bar.value = smooth_progress_state["displayed"]

                if smooth_progress_state["displayed"] >= 0.995:
                    progress_percent_text.value = "Complete"
                else:
                    progress_percent_text.value = f"{smooth_progress_state['displayed'] * 100:.1f}%"

                detail = smooth_progress_state.get("detail", "Working...")

                if download_in_progress["active"] and not detail.endswith("..."):
                    progress_detail_text.value = f"{detail}{dots}"
                else:
                    progress_detail_text.value = detail

                page.update()
                time.sleep(0.12)

        threading.Thread(target=animator, daemon=True).start()

    def stop_progress_animator():
        smooth_progress_state["target"] = 1.0
        smooth_progress_state["active"] = False

    def show_progress_start(mode):
        is_playlist_mode = mode in ["Audio Playlist", "Video Playlist"]

        download_progress_state["is_playlist"] = is_playlist_mode
        download_progress_state["completed"] = 0
        download_progress_state["total"] = 0
        download_progress_state["current_index"] = 0

        progress_panel.visible = True
        progress_bar.value = 0
        progress_percent_text.value = "0%"
        progress_detail_text.value = f"Starting {mode}..."
        status_text.value = f"Starting {mode}..."
        status_text.color = "#BDBDBD"

        start_progress_animator()
        page.update()
    def progress_hook(d):
        status = d.get("status")
        info = d.get("info_dict") or {}

        filename = d.get("filename") or d.get("tmpfilename") or ""
        short_name = Path(filename).name if filename else info.get("title", "Current file")

        playlist_index = info.get("playlist_index")
        playlist_count = (
            info.get("playlist_count")
            or info.get("n_entries")
            or info.get("__last_playlist_index")
        )

        if playlist_count:
            try:
                download_progress_state["total"] = int(playlist_count)
            except Exception:
                pass

        if playlist_index:
            try:
                download_progress_state["current_index"] = int(playlist_index)
            except Exception:
                pass

        is_playlist_mode = download_progress_state["is_playlist"]
        current_index = download_progress_state["current_index"]
        total_items = download_progress_state["total"]

        item_label = ""

        if is_playlist_mode and current_index and total_items:
            item_label = f"Item {current_index}/{total_items}"
        elif is_playlist_mode and current_index:
            item_label = f"Item {current_index}"

        if status == "downloading":
            current_file_value, current_file_percent = safe_percent_from_hook(d)

            progress_panel.visible = True

            speed = strip_ansi(d.get("_speed_str"))
            eta = strip_ansi(d.get("_eta_str"))

            if is_playlist_mode and current_index and total_items:
                if current_file_value is None:
                    current_file_value = 0

                overall_value = ((current_index - 1) + current_file_value) / total_items
                overall_value = max(0, min(overall_value, 1))
                overall_percent = f"{overall_value * 100:.1f}%"

                detail_parts = [
                    f"{item_label}",
                    f"Current file: {current_file_percent}",
                    short_name,
                ]

                if speed:
                    detail_parts.append(f"Speed: {speed}")

                if eta:
                    detail_parts.append(f"ETA: {eta}")

                set_progress_target(overall_value, "  •  ".join(detail_parts))
                status_text.value = f"Downloading playlist... {overall_percent} overall"
                status_text.color = "#BDBDBD"

            else:
                if current_file_value is None:
                    current_file_value = 0.02

                detail_parts = [short_name]

                if speed:
                    detail_parts.append(f"Speed: {speed}")

                if eta:
                    detail_parts.append(f"ETA: {eta}")

                set_progress_target(current_file_value, "  •  ".join(detail_parts))
                status_text.value = f"Downloading... {current_file_percent}"
                status_text.color = "#BDBDBD"

            page.update()

        elif status == "finished":
            progress_panel.visible = True

            if is_playlist_mode and current_index and total_items:
                download_progress_state["completed"] = max(
                    download_progress_state["completed"],
                    current_index,
                )

                completed_items = download_progress_state["completed"]
                overall_value = completed_items / total_items
                overall_value = max(0, min(overall_value, 1))

                set_progress_target(
                    overall_value,
                    f"{item_label} downloaded. Processing with FFmpeg: {short_name}",
                )

                status_text.value = f"Processing item {completed_items}/{total_items} with FFmpeg..."
                status_text.color = "#BDBDBD"

            else:
                set_progress_target(1.0, f"Finished download: {short_name}")
                status_text.value = "Processing with FFmpeg..."
                status_text.color = "#BDBDBD"

            page.update()
    def build_ydl_options(mode):
        selected_quality = quality_dropdown.value
        ffmpeg_location = get_updated_ffmpeg_location() or get_ffmpeg_location()
        downloads_path = Path.home() / "Downloads"
        app_downloads_path = downloads_path / APP_NAME

        is_audio = mode in ["Audio", "Audio Playlist"]
        is_playlist = mode in ["Audio Playlist", "Video Playlist"]

        if mode == "Audio":
            output_template = app_downloads_path / "Audio" / "%(title)s.%(ext)s"
        elif mode == "Video":
            output_template = app_downloads_path / "Video" / "%(title)s.%(ext)s"
        elif mode == "Audio Playlist":
            output_template = app_downloads_path / "Audio Playlist" / "%(playlist_title)s" / "%(playlist_index)03d - %(title)s.%(ext)s"
        elif mode == "Video Playlist":
            output_template = app_downloads_path / "Video Playlist" / "%(playlist_title)s" / "%(playlist_index)03d - %(title)s.%(ext)s"
        else:
            output_template = app_downloads_path / "%(title)s.%(ext)s"

        ydl_opts = {
            "outtmpl": str(output_template),
            "progress_hooks": [progress_hook],
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "logger": AppLogger(),
            "ignoreerrors": is_playlist,
            "retries": 3,
            "fragment_retries": 3,
            "extractor_retries": 3,
        }

        if ffmpeg_location:
            ydl_opts["ffmpeg_location"] = ffmpeg_location

        if is_audio:
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            })
        else:
            ydl_opts.update({
                "format": f"{get_format_string(selected_quality)}/best",
                "merge_output_format": "mp4",
            })

        if is_playlist:
            ydl_opts["noplaylist"] = False
        else:
            ydl_opts["noplaylist"] = True
            ydl_opts["playlist_items"] = "1"

        return ydl_opts
    def run_download(mode):
        if download_in_progress["active"]:
            set_status("A download is already running. Please wait for it to finish.", "#FFCC80")
            return

        if not url_input.value:
            set_status("Error: No URL provided.", "#EF5350")
            return

        download_in_progress["active"] = True

        reset_log()
        show_progress_start(mode)

        if mode in ["Audio Playlist", "Video Playlist"]:
            set_status(f"Starting {mode}. Broken/unavailable items will be skipped.")
        else:
            set_status(f"Starting {mode}. Single item mode is enabled.")

        page.update()

        def worker():
            try:
                ydl_opts = build_ydl_options(mode)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url_input.value])

                progress_panel.visible = True
                progress_bar.value = 1
                progress_percent_text.value = "Complete"

                total_items = download_progress_state.get("total", 0)
                completed_items = download_progress_state.get("completed", 0)

                if download_progress_state.get("is_playlist") and total_items:
                    progress_detail_text.value = f"Complete — {completed_items}/{total_items} items processed."
                else:
                    progress_detail_text.value = "Complete."

                if warning_count["count"] > 0:
                    set_status(
                        f"Complete with {warning_count['count']} skipped/error item(s).",
                        "#FFCC80",
                    )
                else:
                    set_status("Success! Check your Downloads folder.", "#66BB6A")

            except Exception as ex:
                stop_progress_animator()
                append_log(str(ex), count_warning=True)
                set_status(f"Error: {str(ex)[:160]}", "#EF5350")

            finally:
                download_in_progress["active"] = False
                page.update()

        threading.Thread(target=worker, daemon=True).start()
    def icon_control(mode):
        icon_path = icon_cache.get(mode)

        if icon_path:
            return ft.Image(
                src=str(icon_path),
                width=92,
                height=92,
                fit="contain",
            )

        return ft.Container(
            width=92,
            height=92,
            alignment=ft.alignment.center,
            content=ft.Text("?", size=34, weight="bold"),
        )

    def build_button_card(label, mode):
        return ft.Container(
            width=260,
            height=190,
            padding=16,
            border_radius=18,
            bgcolor="#1E1E1E",
            content=ft.Column(
                [
                    icon_control(mode),
                    ft.Text(label, weight="bold", size=14, color="#FFFFFF"),
                    ft.ElevatedButton(
                        "DOWNLOAD",
                        width=165,
                        on_click=lambda _: run_download(mode),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
        )

    def toggle_platforms(e):
        platforms_list.visible = not platforms_list.visible
        show_platforms_btn.text = (
            "Hide Sites" if platforms_list.visible else "Show Supported Sites"
        )
        page.update()


    update_state = {
        "release": None,
        "asset": None,
    }

    update_status_text = ft.Text(
        value="",
        size=10,
        color="#9E9E9E",
        text_align=ft.TextAlign.CENTER,
        width=620,
    )

    update_progress_ring = ft.ProgressRing(
        width=18,
        height=18,
        stroke_width=2,
        visible=False,
    )

    def set_update_busy(is_busy):
        update_progress_ring.visible = is_busy
        update_button.disabled = is_busy

        try:
            page.update()
        except Exception:
            pass

    def set_update_status(message, color="#9E9E9E"):
        update_status_text.value = message
        update_status_text.color = color

        try:
            page.update()
        except Exception:
            pass

    def reset_update_button():
        update_button.text = "Check for Updates"
        update_button.on_click = check_for_updates_clicked
        update_button.disabled = False

        try:
            page.update()
        except Exception:
            pass

    def check_for_updates_clicked(e=None):
        threading.Thread(
            target=lambda: check_for_updates(silent=False),
            daemon=True,
        ).start()

    def install_update_clicked(e=None):
        threading.Thread(
            target=install_update,
            daemon=True,
        ).start()

    def check_for_updates(silent=False):
        try:
            if not silent:
                set_update_status("Checking for updates...", "#90CAF9")
                set_update_busy(True)

            release_data = github_request_json(GITHUB_LATEST_RELEASE_API)
            latest_version = release_data.get("tag_name") or release_data.get("name") or ""

            if not is_newer_version(latest_version, APP_VERSION):
                if not silent:
                    set_update_status(f"You're up to date. Current version: v{APP_VERSION}", "#81C784")
                reset_update_button()
                return

            asset = find_update_asset(release_data)

            if not asset:
                set_update_status(
                    f"Update {latest_version} found, but no installer EXE was attached.",
                    "#FFCC80",
                )
                reset_update_button()
                return

            update_state["release"] = release_data
            update_state["asset"] = asset

            update_button.text = "Install Update"
            update_button.on_click = install_update_clicked
            update_button.disabled = False

            set_update_status(f"Update available: {latest_version}", "#FFCC80")

        except urllib.error.HTTPError as ex:
            if not silent:
                if ex.code == 404:
                    set_update_status("No GitHub release found yet.", "#FFCC80")
                else:
                    set_update_status(f"Update check failed: HTTP {ex.code}", "#EF5350")
                reset_update_button()

        except Exception as ex:
            if not silent:
                set_update_status(f"Update check failed: {str(ex)[:80]}", "#EF5350")
                reset_update_button()

        finally:
            set_update_busy(False)

    def install_update():
        asset = update_state.get("asset")

        if not asset:
            check_for_updates(silent=False)
            asset = update_state.get("asset")

            if not asset:
                return

        try:
            set_update_busy(True)

            asset_name = asset.get("name") or "VibeDownloaderProSetup.exe"
            asset_name = re.sub(r"[^A-Za-z0-9_. -]", "_", asset_name)

            download_url = asset.get("browser_download_url")
            if not download_url:
                raise RuntimeError("Missing installer download URL.")

            updates_dir = Path.home() / "Downloads" / APP_NAME / "Updates"
            updates_dir.mkdir(parents=True, exist_ok=True)

            installer_path = updates_dir / asset_name

            set_update_status("Downloading update...", "#90CAF9")

            request = urllib.request.Request(
                download_url,
                headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}"},
            )

            with urllib.request.urlopen(request, timeout=60) as response:
                total_size = int(response.headers.get("Content-Length") or 0)
                downloaded_size = 0

                with open(installer_path, "wb") as output_file:
                    while True:
                        chunk = response.read(1024 * 256)

                        if not chunk:
                            break

                        output_file.write(chunk)
                        downloaded_size += len(chunk)

                        if total_size:
                            percent = downloaded_size / total_size * 100
                            set_update_status(f"Downloading update... {percent:.0f}%", "#90CAF9")

            set_update_status("Launching installer...", "#81C784")

            subprocess.Popen([str(installer_path)], shell=False)

            time.sleep(1)
            os._exit(0)

        except Exception as ex:
            set_update_status(f"Update install failed: {str(ex)[:80]}", "#EF5350")
            reset_update_button()
            set_update_busy(False)

    update_button = ft.ElevatedButton(
        "Check for Updates",
        on_click=check_for_updates_clicked,
        width=250,
    )

    update_panel = ft.Column(
        [
            ft.Row(
                [
                    update_button,
                    update_progress_ring,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
            update_status_text,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=4,
    )


    tool_status_text = ft.Text(
        value="",
        size=10,
        color="#9E9E9E",
        text_align=ft.TextAlign.CENTER,
        width=620,
    )

    tool_progress_ring = ft.ProgressRing(
        width=18,
        height=18,
        stroke_width=2,
        visible=False,
    )

    def set_tool_busy(is_busy):
        tool_progress_ring.visible = is_busy
        tool_update_button.disabled = is_busy

        try:
            page.update()
        except Exception:
            pass

    def set_tool_status(message, color="#9E9E9E"):
        tool_status_text.value = message
        tool_status_text.color = color

        try:
            page.update()
        except Exception:
            pass

    def check_tool_updates_clicked(e=None):
        threading.Thread(
            target=install_tool_updates,
            daemon=True,
        ).start()

    def install_tool_updates():
        tools_dir = get_user_tools_dir()
        temp_dir = tools_dir.parent / "_tool_update_temp"
        backup_dir = tools_dir.parent / "_tool_update_backup"

        updated_tools = []
        warnings_list = []

        try:
            set_tool_busy(True)
            set_tool_status("Checking tool updates...", "#90CAF9")

            tools_dir.mkdir(parents=True, exist_ok=True)

            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

            if backup_dir.exists():
                shutil.rmtree(backup_dir, ignore_errors=True)

            temp_dir.mkdir(parents=True, exist_ok=True)
            backup_dir.mkdir(parents=True, exist_ok=True)

            for tool_name in TOOL_EXE_NAMES:
                existing_tool = tools_dir / tool_name

                if existing_tool.exists():
                    shutil.copy2(existing_tool, backup_dir / tool_name)

            def show_download_progress(label):
                def inner(downloaded_size, total_size):
                    percent = downloaded_size / total_size * 100
                    set_tool_status(f"{label}... {percent:.0f}%", "#90CAF9")
                return inner

            set_tool_status("Downloading yt-dlp...", "#90CAF9")

            ytdlp_temp = temp_dir / "yt-dlp.exe"
            download_url_to_file(
                YTDLP_EXE_DOWNLOAD_URL,
                ytdlp_temp,
                show_download_progress("Downloading yt-dlp"),
            )

            validate_tool(ytdlp_temp, ["--version"])
            shutil.copy2(ytdlp_temp, tools_dir / "yt-dlp.exe")
            updated_tools.append("yt-dlp")

            try:
                set_tool_status("Checking for FFmpeg tools bundle...", "#90CAF9")

                release_data = github_request_json(GITHUB_LATEST_RELEASE_API)
                bundle_asset = find_tools_bundle_asset(release_data)

                if bundle_asset:
                    bundle_name = bundle_asset.get("name") or "VibeDownloaderProTools.zip"
                    bundle_name = re.sub(r"[^A-Za-z0-9_. -]", "_", bundle_name)

                    bundle_path = temp_dir / bundle_name
                    extract_dir = temp_dir / "tools_bundle"

                    set_tool_status("Downloading FFmpeg tools bundle...", "#90CAF9")

                    download_url_to_file(
                        bundle_asset.get("browser_download_url"),
                        bundle_path,
                        show_download_progress("Downloading tools bundle"),
                    )

                    with zipfile.ZipFile(bundle_path, "r") as zip_ref:
                        zip_ref.extractall(extract_dir)

                    ffmpeg_temp = find_file_recursively(extract_dir, "ffmpeg.exe")
                    ffprobe_temp = find_file_recursively(extract_dir, "ffprobe.exe")
                    ytdlp_bundle_temp = find_file_recursively(extract_dir, "yt-dlp.exe")

                    if ffmpeg_temp and ffprobe_temp:
                        validate_tool(ffmpeg_temp, ["-version"])
                        validate_tool(ffprobe_temp, ["-version"])

                        shutil.copy2(ffmpeg_temp, tools_dir / "ffmpeg.exe")
                        shutil.copy2(ffprobe_temp, tools_dir / "ffprobe.exe")

                        updated_tools.append("ffmpeg")
                        updated_tools.append("ffprobe")
                    else:
                        warnings_list.append("No ffmpeg/ffprobe found in tools bundle.")

                    if ytdlp_bundle_temp:
                        validate_tool(ytdlp_bundle_temp, ["--version"])
                        shutil.copy2(ytdlp_bundle_temp, tools_dir / "yt-dlp.exe")

                else:
                    warnings_list.append("No tools ZIP found in GitHub Release yet.")

            except Exception as bundle_ex:
                warnings_list.append(f"Tools bundle skipped: {str(bundle_ex)[:80]}")

            if not updated_tools:
                raise RuntimeError("No tools were updated.")

            status = "Updated: " + ", ".join(sorted(set(updated_tools)))

            if warnings_list:
                status += " | " + " ".join(warnings_list)

            set_tool_status(status, "#81C784")

        except Exception as ex:
            try:
                for tool_name in TOOL_EXE_NAMES:
                    backup_tool = backup_dir / tool_name

                    if backup_tool.exists():
                        shutil.copy2(backup_tool, tools_dir / tool_name)
            except Exception:
                pass

            set_tool_status(f"Tool update failed: {str(ex)[:90]}", "#EF5350")

        finally:
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

            set_tool_busy(False)

    tool_update_button = ft.ElevatedButton(
        "Check Tool Updates",
        on_click=check_tool_updates_clicked,
        width=250,
    )

    tool_update_panel = ft.Column(
        [
            ft.Row(
                [
                    tool_update_button,
                    tool_progress_ring,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
            tool_status_text,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=4,
    )

    show_platforms_btn = ft.ElevatedButton(
        "Show Supported Sites",
        on_click=toggle_platforms,
        width=250,
    )

    platforms_list = ft.Column(
        [
            ft.Text(f"• {platform}", size=11, color="#E0E0E0")
            for platform in SUPPORTED_PLATFORMS
        ],
        visible=False,
    )

    ffmpeg_status = f"Version v{APP_VERSION}"

    page.add(
        ft.Column(
            [
                ft.Text(APP_NAME, size=36, weight="bold", color="#90CAF9"),
                ft.Divider(height=10, color="transparent"),
                url_input,
                quality_dropdown,
                ft.Divider(height=10, color="transparent"),
                ft.Row(
                    [
                        build_button_card("AUDIO", "Audio"),
                        build_button_card("VIDEO", "Video"),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=28,
                ),
                ft.Row(
                    [
                        build_button_card("AUDIO PLAYLIST", "Audio Playlist"),
                        build_button_card("VIDEO PLAYLIST", "Video Playlist"),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=28,
                ),
                ft.Divider(height=10, color="transparent"),
                progress_panel,
                status_text,
                log_panel,
                ft.Divider(height=8, color="transparent"),
                update_panel,
                ft.Divider(height=4, color="transparent"),
                tool_update_panel,
                ft.Divider(height=4, color="transparent"),
                show_platforms_btn,
                platforms_list,
                ft.Divider(height=6, color="transparent"),
                ft.Text(ffmpeg_status, size=9, color="#757575"),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=9,
        )
    )


    threading.Thread(target=lambda: (time.sleep(1.5), check_for_updates(silent=True)), daemon=True).start()

if __name__ == "__main__":
    configure_windows_app_identity()
    ft.app(target=main)








