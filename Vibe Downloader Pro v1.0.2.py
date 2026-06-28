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
APP_VERSION = "1.0.2"
APP_ID = "InFiniteStudios.VibeDownloaderPro.v102"
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


def get_video_format_string(selected_quality, selected_video_format):
    height_filter = ""

    if selected_quality and selected_quality != "best":
        height_filter = f"[height<={selected_quality}]"

    if selected_video_format == "mp4":
        return (
            f"bestvideo{height_filter}[ext=mp4]+bestaudio[ext=m4a]/"
            f"bestvideo{height_filter}+bestaudio/"
            f"best{height_filter}[ext=mp4]/best{height_filter}/best"
        )

    if selected_video_format == "webm":
        return (
            f"bestvideo{height_filter}[ext=webm]+bestaudio[ext=webm]/"
            f"bestvideo{height_filter}+bestaudio/"
            f"best{height_filter}[ext=webm]/best{height_filter}/best"
        )

    if selected_video_format == "mkv":
        return f"bestvideo{height_filter}+bestaudio/best{height_filter}/best"

    return f"bestvideo{height_filter}+bestaudio/best{height_filter}/best"


def get_audio_quality_value(selected_audio_quality):
    if selected_audio_quality == "best":
        return "0"

    return selected_audio_quality or "192"


def parse_urls_from_text(value):
    if not value:
        return []

    candidates = re.split(r"\s+", value.strip())
    urls = []

    for candidate in candidates:
        cleaned = candidate.strip()

        if cleaned:
            urls.append(cleaned)

    return urls


def strip_ansi(value):
    if value is None:
        return ""

    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", str(value)).strip()


def is_youtube_url(value):
    cleaned = str(value or "").lower()
    return "youtube.com" in cleaned or "youtu.be" in cleaned


def is_youtube_auth_error(value):
    cleaned = strip_ansi(value).lower()

    trigger_phrases = [
        "sign in to confirm",
        "not a bot",
        "use --cookies-from-browser",
        "cookies for the authentication",
        "confirm you're not a bot",
        "confirm you are not a bot",
    ]

    return any(phrase in cleaned for phrase in trigger_phrases)


def clean_download_error_message(value):
    cleaned = strip_ansi(value)

    if is_youtube_auth_error(cleaned):
        return (
            "YouTube requested sign-in / bot verification. "
            "The app tried browser cookies where possible. "
            "Failed jobs stayed saved in the queue for retry."
        )

    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if len(cleaned) > 220:
        cleaned = cleaned[:217] + "..."

    return cleaned


def get_auto_cookie_browsers():
    return ["edge", "chrome", "brave", "firefox"]


def get_cookie_browser_label(browser_name):
    labels = {
        "edge": "Edge",
        "chrome": "Chrome",
        "brave": "Brave",
        "firefox": "Firefox",
    }

    return labels.get(browser_name, browser_name)


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
    page.scroll = ft.ScrollMode.AUTO
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
    QUEUE_MODES = ["Audio", "Video", "Audio Playlist", "Video Playlist"]
    download_queues = {mode: [] for mode in QUEUE_MODES}
    download_progress_state = {
        "is_playlist": False,
        "completed": 0,
        "total": 0,
        "current_index": 0,
    }
    download_error_state = {
        "youtube_auth": False,
    }
    smooth_progress_state = {
        "active": False,
        "target": 0.0,
        "displayed": 0.0,
        "detail": "Waiting...",
        "last_ui_update": 0.0,
    }

    url_input = ft.TextField(
        label="Paste URL(s) Here",
        hint_text="Paste one URL or multiple URLs",
        autofocus=True,
        width=620,
    )

    audio_quality_dropdown = ft.Dropdown(
        label="Audio Quality",
        width=260,
        options=[
            ft.dropdown.Option("best", text="Best Quality"),
            ft.dropdown.Option("320", text="320 kbps"),
            ft.dropdown.Option("256", text="256 kbps"),
            ft.dropdown.Option("192", text="192 kbps"),
            ft.dropdown.Option("128", text="128 kbps"),
        ],
        value="best",
    )

    audio_format_dropdown = ft.Dropdown(
        label="Audio Format",
        width=260,
        options=[
            ft.dropdown.Option("mp3", text="MP3"),
            ft.dropdown.Option("m4a", text="M4A"),
            ft.dropdown.Option("opus", text="OPUS"),
            ft.dropdown.Option("wav", text="WAV"),
            ft.dropdown.Option("flac", text="FLAC"),
        ],
        value="mp3",
    )

    video_quality_dropdown = ft.Dropdown(
        label="Video Quality",
        width=260,
        options=[
            ft.dropdown.Option("best", text="Best Quality"),
            ft.dropdown.Option("2160", text="2160p / 4K"),
            ft.dropdown.Option("1440", text="1440p / 2K"),
            ft.dropdown.Option("1080", text="1080p"),
            ft.dropdown.Option("720", text="720p"),
            ft.dropdown.Option("480", text="480p"),
            ft.dropdown.Option("360", text="360p"),
        ],
        value="best",
    )

    video_format_dropdown = ft.Dropdown(
        label="Video Format",
        width=260,
        options=[
            ft.dropdown.Option("auto", text="Best / Auto"),
            ft.dropdown.Option("mp4", text="MP4"),
            ft.dropdown.Option("webm", text="WEBM"),
            ft.dropdown.Option("mkv", text="MKV"),
        ],
        value="mp4",
    )

    queue_speed_dropdown = ft.Dropdown(
        label="Queue Speed",
        width=260,
        options=[
            ft.dropdown.Option("normal", text="Normal"),
            ft.dropdown.Option("gentle", text="Gentle / Fewer Bot Checks"),
        ],
        value="normal",
    )

    queue_count_text = ft.Text(
        value="Queued links: 0",
        size=12,
        color="#BDBDBD",
        text_align=ft.TextAlign.CENTER,
        width=620,
    )

    queue_preview_text = ft.Text(
        value="No queued links yet.",
        size=10,
        color="#9E9E9E",
        text_align=ft.TextAlign.CENTER,
        width=620,
        selectable=True,
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

    def safe_page_update():
        try:
            page.update()
        except Exception:
            pass

    def run_background_task(target):
        try:
            page.run_thread(target)
        except Exception:
            threading.Thread(target=target, daemon=True).start()

    def set_status(message, color="#BDBDBD"):
        status_text.value = message
        status_text.color = color
        safe_page_update()

    def reset_log():
        download_log_entries.clear()
        warning_count["count"] = 0
        log_title.visible = False
        log_text.visible = False
        log_panel.visible = False
        log_text.value = ""

    def append_log(message, count_warning=True):
        cleaned = clean_download_error_message(message)

        if not cleaned:
            return

        if count_warning:
            warning_count["count"] += 1

        if cleaned in download_log_entries:
            return

        download_log_entries.append(cleaned)

        if len(download_log_entries) > 12:
            download_log_entries.pop(0)

        log_text.value = "\n".join(f"- {entry}" for entry in download_log_entries)
        log_title.visible = True
        log_text.visible = True
        log_panel.visible = True

        try:
            safe_page_update()
        except Exception:
            pass



    def get_download_root():

        downloads_path = Path.home() / "Downloads"
        app_downloads_path = downloads_path / APP_NAME
        app_downloads_path.mkdir(parents=True, exist_ok=True)
        return app_downloads_path

    def get_queue_cache_path():
        cache_dir = get_download_root() / "_app_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / "queue_cache.json"

    def get_current_queue_settings(mode):
        return {
            "audio_quality": audio_quality_dropdown.value or "best",
            "audio_format": audio_format_dropdown.value or "mp3",
            "video_quality": video_quality_dropdown.value or "best",
            "video_format": video_format_dropdown.value or "mp4",
        }

    def make_queue_job(mode, url):
        settings = get_current_queue_settings(mode)

        return {
            "mode": mode,
            "url": url,
            "audio_quality": settings["audio_quality"],
            "audio_format": settings["audio_format"],
            "video_quality": settings["video_quality"],
            "video_format": settings["video_format"],
            "status": "pending",
            "added_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def get_audio_quality_label(value):
        labels = {
            "best": "Best Quality",
            "320": "320 kbps",
            "256": "256 kbps",
            "192": "192 kbps",
            "128": "128 kbps",
        }

        return labels.get(value, value or "192 kbps")

    def get_video_quality_label(value):
        labels = {
            "best": "Best Quality",
            "2160": "2160p / 4K",
            "1440": "1440p / 2K",
            "1080": "1080p",
            "720": "720p",
            "480": "480p",
            "360": "360p",
        }

        return labels.get(value, value or "Best Quality")

    def job_summary(job):
        mode = job.get("mode", "")
        url = job.get("url", "")

        if len(url) > 58:
            url = url[:55] + "..."

        status_prefix = "FAILED | " if job.get("status") == "failed" else ""

        if mode in ["Audio", "Audio Playlist"]:
            quality = get_audio_quality_label(job.get("audio_quality"))
            fmt = (job.get("audio_format") or "mp3").upper()
            return f"{status_prefix}{fmt} | {quality} | {url}"

        quality = get_video_quality_label(job.get("video_quality"))
        fmt = (job.get("video_format") or "mp4").upper()
        return f"{status_prefix}{fmt} | {quality} | {url}"

    queue_count_texts = {}

    queue_preview_texts = {}

    def save_queue_cache():
        try:
            cache_path = get_queue_cache_path()
            temp_path = cache_path.with_suffix(".tmp")

            payload = {
                "schema_version": 1,
                "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "queues": download_queues,
            }

            with open(temp_path, "w", encoding="utf-8") as cache_file:
                json.dump(payload, cache_file, indent=2)

            os.replace(temp_path, cache_path)

        except Exception as ex:
            append_log(f"Queue cache save failed: {str(ex)[:120]}", count_warning=True)

    def load_queue_cache():
        try:
            cache_path = get_queue_cache_path()

            if not cache_path.exists():
                return 0

            with open(cache_path, "r", encoding="utf-8") as cache_file:
                payload = json.load(cache_file)

            queues = payload.get("queues") or {}
            recovered = 0

            for mode in QUEUE_MODES:
                download_queues[mode].clear()

                for job in queues.get(mode, []):
                    if isinstance(job, dict) and job.get("url"):
                        job["mode"] = mode
                        download_queues[mode].append(job)
                        recovered += 1

            return recovered

        except Exception as ex:
            append_log(f"Queue cache load failed: {str(ex)[:120]}", count_warning=True)
            return 0

    def update_queue_display():
        for mode in QUEUE_MODES:
            queue = download_queues.get(mode, [])
            count_text = queue_count_texts.get(mode)
            preview_text = queue_preview_texts.get(mode)

            if count_text:
                count_text.value = f"Queued: {len(queue)}"

            if preview_text:
                if queue:
                    preview_items = []

                    for index, job in enumerate(queue[:4], start=1):
                        preview_items.append(f"{index}. {job_summary(job)}")

                    if len(queue) > 4:
                        preview_items.append(f"...and {len(queue) - 4} more")

                    preview_text.value = "\n".join(preview_items)
                else:
                    preview_text.value = "No queued links."

        try:
            safe_page_update()
        except Exception:
            pass

    def add_to_queue(mode, e=None):
        urls = parse_urls_from_text(url_input.value)

        if not urls:
            set_status("Paste one or more URLs first.", "#FFCC80")
            return

        added_count = 0

        for url in urls:
            duplicate = any(existing.get("url") == url for existing in download_queues[mode])

            if not duplicate:
                download_queues[mode].append(make_queue_job(mode, url))
                added_count += 1

        url_input.value = ""
        save_queue_cache()
        update_queue_display()

        if added_count == 1:
            set_status(f"Added 1 link to the {mode} queue.", "#90CAF9")
        else:
            set_status(f"Added {added_count} links to the {mode} queue.", "#90CAF9")

    def clear_queue(mode, e=None):
        download_queues[mode].clear()
        save_queue_cache()
        update_queue_display()
        set_status(f"{mode} queue cleared.", "#BDBDBD")

    def build_queue_panel(mode, title):
        count_text = ft.Text(
            value="Queued: 0",
            size=11,
            color="#BDBDBD",
            text_align=ft.TextAlign.CENTER,
            width=280,
        )

        preview_text = ft.Text(
            value="No queued links.",
            size=9,
            color="#9E9E9E",
            text_align=ft.TextAlign.CENTER,
            width=280,
            selectable=True,
        )

        queue_count_texts[mode] = count_text
        queue_preview_texts[mode] = preview_text

        return ft.Container(
            width=300,
            padding=10,
            border_radius=16,
            bgcolor="#101418",
            content=ft.Column(
                [
                    ft.Text(
                        title,
                        size=12,
                        weight="bold",
                        color="#90CAF9",
                        text_align=ft.TextAlign.CENTER,
                        width=280,
                    ),
                    count_text,
                    preview_text,
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Download Queue",
                                on_click=lambda _, m=mode: run_download(m, use_queue=True),
                                width=135,
                            ),
                            ft.ElevatedButton(
                                "Clear",
                                on_click=lambda _, m=mode: clear_queue(m),
                                width=85,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            ),
        )

    audio_queue_panel = build_queue_panel("Audio", "AUDIO QUEUE")
    video_queue_panel = build_queue_panel("Video", "VIDEO QUEUE")
    audio_playlist_queue_panel = build_queue_panel("Audio Playlist", "AUDIO PLAYLIST QUEUE")
    video_playlist_queue_panel = build_queue_panel("Video Playlist", "VIDEO PLAYLIST QUEUE")

    recovered_jobs = load_queue_cache()
    update_queue_display()

    if recovered_jobs:
        status_text.value = f"Recovered {recovered_jobs} queued job(s) from the last session."
        status_text.color = "#90CAF9"
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

            if is_youtube_auth_error(cleaned):
                download_error_state["youtube_auth"] = True
                append_log(
                    "YouTube requested sign-in / bot verification. Retrying with signed-in browser cookies if possible.",
                    count_warning=True,
                )
                return

            if cleaned:
                append_log(f"Skipped/Error: {cleaned}", count_warning=True)

    def clamp_progress(value):

        try:
            value = float(value)
        except Exception:
            value = 0.0

        return max(0.0, min(value, 1.0))

    def set_progress_target(value, detail=None, force=False):
        value = clamp_progress(value)

        smooth_progress_state["target"] = value
        smooth_progress_state["displayed"] = value

        progress_bar.value = value

        if value >= 0.995:
            progress_percent_text.value = "Complete"
        else:
            progress_percent_text.value = f"{value * 100:.1f}%"

        if detail is not None:
            smooth_progress_state["detail"] = detail
            progress_detail_text.value = detail

        now = time.time()
        last_update = smooth_progress_state.get("last_ui_update", 0.0)

        if force or (now - last_update) >= 0.08:
            smooth_progress_state["last_ui_update"] = now

            try:
                safe_page_update()
            except Exception:
                pass

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

                safe_page_update()
                time.sleep(0.05)

        run_background_task(animator)

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
        safe_page_update()
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

                set_progress_target(overall_value, "  |  ".join(detail_parts), force=True)
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

                set_progress_target(current_file_value, "  |  ".join(detail_parts), force=True)
                status_text.value = f"Downloading... {current_file_percent}"
                status_text.color = "#BDBDBD"

            safe_page_update()

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
                    force=True,
                )

                status_text.value = f"Processing item {completed_items}/{total_items} with FFmpeg..."
                status_text.color = "#BDBDBD"

            else:
                set_progress_target(1.0, f"Finished download: {short_name}", force=True)
                status_text.value = "Processing with FFmpeg..."
                status_text.color = "#BDBDBD"

            safe_page_update()
    def build_ydl_options(mode, settings=None, browser_cookie_source=None):
        if settings is None:
            settings = get_current_queue_settings(mode)

        selected_audio_quality = settings.get("audio_quality") or "best"
        selected_audio_format = settings.get("audio_format") or "mp3"
        selected_video_quality = settings.get("video_quality") or "best"
        selected_video_format = settings.get("video_format") or "mp4"

        ffmpeg_location = get_updated_ffmpeg_location() or get_ffmpeg_location()
        app_downloads_path = get_download_root()

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

        if queue_speed_dropdown.value == "gentle":
            ydl_opts["sleep_interval_requests"] = 0.75
            ydl_opts["sleep_interval"] = 5
            ydl_opts["max_sleep_interval"] = 12

        if browser_cookie_source:
            ydl_opts["cookiesfrombrowser"] = (browser_cookie_source, None, None, None)

        if ffmpeg_location:
            ydl_opts["ffmpeg_location"] = ffmpeg_location

        if is_audio:
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": selected_audio_format,
                        "preferredquality": get_audio_quality_value(selected_audio_quality),
                    }
                ],
            })
        else:
            ydl_opts["format"] = get_video_format_string(selected_video_quality, selected_video_format)

            if selected_video_format in ["mp4", "webm", "mkv"]:
                ydl_opts["merge_output_format"] = selected_video_format

        if is_playlist:
            ydl_opts["noplaylist"] = False
        else:
            ydl_opts["noplaylist"] = True
            ydl_opts["playlist_items"] = "1"

        return ydl_opts

    def download_job_with_auto_retries(mode, job, current_url, job_label):
        last_error = None

        def try_download(browser_cookie_source=None):
            download_error_state["youtube_auth"] = False

            ydl_opts = build_ydl_options(
                mode,
                job,
                browser_cookie_source=browser_cookie_source,
            )

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([current_url])

            if download_error_state.get("youtube_auth"):
                raise RuntimeError("YouTube requested sign-in / bot verification.")

        try:
            try_download()
            return True, None

        except Exception as first_ex:
            last_error = first_ex

            if not is_youtube_auth_error(str(first_ex)):
                return False, clean_download_error_message(first_ex)

            set_status(
                "YouTube requested sign-in / bot verification. Retrying with browser cookies...",
                "#FFCC80",
            )
            append_log(
                "YouTube requested sign-in / bot verification. Retrying with signed-in browser cookies if possible.",
                count_warning=False,
            )

            for browser_name in get_auto_cookie_browsers():
                browser_label = get_cookie_browser_label(browser_name)

                try:
                    set_status(f"Retrying {job_label} using {browser_label} cookies...", "#FFCC80")
                    set_progress_target(0.05, f"Trying {browser_label} cookies", force=True)

                    try_download(browser_cookie_source=browser_name)

                    append_log(f"Cookie retry succeeded using {browser_label}.", count_warning=False)
                    return True, None

                except Exception as cookie_ex:
                    last_error = cookie_ex
                    continue

            return False, clean_download_error_message(last_error)

    def run_download(mode, use_queue=False):
        if download_in_progress["active"]:
            set_status("A download is already running. Please wait for it to finish.", "#FFCC80")
            return

        if use_queue:
            jobs_to_download = list(download_queues[mode])

            if not jobs_to_download:
                set_status(f"{mode} queue is empty.", "#FFCC80")
                return
        else:
            urls_to_download = parse_urls_from_text(url_input.value)

            if not urls_to_download:
                set_status("Error: No URL provided.", "#EF5350")
                return

            jobs_to_download = [make_queue_job(mode, url) for url in urls_to_download]

        download_in_progress["active"] = True

        reset_log()
        show_progress_start(mode)

        total_jobs = len(jobs_to_download)

        if use_queue:
            set_status(f"Starting {mode} queue: {total_jobs} job(s).")
        elif total_jobs > 1:
            set_status(f"Starting {mode}: {total_jobs} pasted links.")
        elif mode in ["Audio Playlist", "Video Playlist"]:
            set_status(f"Starting {mode}. Broken/unavailable items will be skipped.")
        else:
            set_status(f"Starting {mode}. Single item mode is enabled.")

        safe_page_update()

        def worker():
            failed_jobs = []
            success_count = 0

            try:
                for index, job in enumerate(jobs_to_download, start=1):
                    current_url = (job.get("url") or "").strip()

                    if not current_url:
                        continue

                    job["status"] = "downloading"
                    job["last_error"] = ""

                    job_label = f"job {index}/{total_jobs}"

                    if total_jobs > 1:
                        set_status(f"{mode}: downloading {job_label}", "#BDBDBD")
                        set_progress_target(0.03, f"Starting {job_label}", force=True)
                        safe_page_update()

                    if queue_speed_dropdown.value == "gentle" and index > 1:
                        set_status("Gentle mode: waiting briefly before next job...", "#BDBDBD")
                        set_progress_target(0.04, "Gentle mode delay", force=True)
                        time.sleep(6)

                    success, error_message = download_job_with_auto_retries(
                        mode,
                        job,
                        current_url,
                        job_label,
                    )

                    if success:
                        success_count += 1
                        job["status"] = "completed"
                        job["last_error"] = ""

                        if use_queue and job in download_queues[mode]:
                            download_queues[mode].remove(job)
                            save_queue_cache()
                            update_queue_display()
                    else:
                        job["status"] = "failed"
                        job["last_error"] = error_message or "Download failed."
                        failed_jobs.append(job)
                        append_log(f"{mode} {job_label} failed: {job['last_error']}", count_warning=True)

                        if not use_queue:
                            duplicate = any(
                                existing.get("url") == job.get("url")
                                for existing in download_queues[mode]
                            )

                            if not duplicate:
                                download_queues[mode].append(job)

                        save_queue_cache()
                        update_queue_display()

                progress_panel.visible = True
                progress_bar.value = 1
                progress_percent_text.value = "Complete"

                total_items = download_progress_state.get("total", 0)
                completed_items = download_progress_state.get("completed", 0)

                if download_progress_state.get("is_playlist") and total_items:
                    progress_detail_text.value = f"Finished playlist: {completed_items}/{total_items} items processed"
                elif total_jobs > 1:
                    progress_detail_text.value = f"Finished jobs: {success_count}/{total_jobs} completed"
                else:
                    progress_detail_text.value = "Download finished"

                if failed_jobs and success_count:
                    set_status(f"Done with warnings: {success_count}/{total_jobs} completed. Failed jobs stayed saved for retry.", "#FFCC80")
                elif failed_jobs and not success_count:
                    set_status("Download failed. Jobs stayed saved for retry.", "#EF5350")
                elif use_queue:
                    set_status(f"Success! Completed {success_count}/{total_jobs} {mode} queued job(s).", "#66BB6A")
                elif total_jobs > 1:
                    set_status(f"Success! Completed {success_count}/{total_jobs} pasted link(s).", "#66BB6A")
                else:
                    set_status("Success! Check your Downloads folder.", "#66BB6A")

                save_queue_cache()
                update_queue_display()

            except Exception as ex:
                set_status(f"Error: {clean_download_error_message(ex)}", "#EF5350")
                save_queue_cache()
                update_queue_display()

            finally:
                download_in_progress["active"] = False
                stop_progress_animator()
                safe_page_update()

        run_background_task(worker)

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
            height=230,
            padding=14,
            bgcolor="#1E1E1E",
            border_radius=18,
            content=ft.Column(
                [
                    icon_control(mode),
                    ft.Text(label, weight="bold", color="#FFFFFF", text_align=ft.TextAlign.CENTER),
                    ft.ElevatedButton(
                        "DOWNLOAD NOW",
                        width=170,
                        on_click=lambda _, m=mode: run_download(m, use_queue=False),
                    ),
                    ft.ElevatedButton(
                        "ADD TO QUEUE",
                        width=170,
                        on_click=lambda _, m=mode: add_to_queue(m),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=7,
            ),
        )

    def toggle_platforms(e):
        platforms_list.visible = not platforms_list.visible
        show_platforms_btn.text = (
            "Hide Sites" if platforms_list.visible else "Show Supported Sites"
        )
        safe_page_update()


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
            safe_page_update()
        except Exception:
            pass

    def set_update_status(message, color="#9E9E9E"):
        update_status_text.value = message
        update_status_text.color = color

        try:
            safe_page_update()
        except Exception:
            pass

    def reset_update_button():
        update_button.text = "Check for Updates"
        update_button.on_click = check_for_updates_clicked
        update_button.disabled = False

        try:
            safe_page_update()
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
            safe_page_update()
        except Exception:
            pass

    def set_tool_status(message, color="#9E9E9E"):
        tool_status_text.value = message
        tool_status_text.color = color

        try:
            safe_page_update()
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
            ft.Text(f"- {platform}", size=11, color="#E0E0E0")
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
                ft.Divider(height=10, color="transparent"),
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("AUDIO SETTINGS", size=12, weight="bold", color="#90CAF9", text_align=ft.TextAlign.CENTER, width=260),
                                ft.Divider(height=4, color="transparent"),
                                audio_quality_dropdown,
                                audio_format_dropdown,
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        ft.Column(
                            [
                                ft.Text("VIDEO SETTINGS", size=12, weight="bold", color="#90CAF9", text_align=ft.TextAlign.CENTER, width=260),
                                ft.Divider(height=4, color="transparent"),
                                video_quality_dropdown,
                                video_format_dropdown,
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=40,
                ),
                ft.Divider(height=12, color="transparent"),
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
                ft.Text("QUEUES", size=14, weight="bold", color="#90CAF9", text_align=ft.TextAlign.CENTER, width=620),
                queue_speed_dropdown,
                ft.Row(
                    [
                        audio_queue_panel,
                        video_queue_panel,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
                ft.Row(
                    [
                        audio_playlist_queue_panel,
                        video_playlist_queue_panel,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
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









