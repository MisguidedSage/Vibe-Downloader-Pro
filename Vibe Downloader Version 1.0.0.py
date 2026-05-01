import flet as ft
import yt_dlp
from pathlib import Path

SUPPORTED_PLATFORMS = [
    "YouTube", "Vimeo", "TikTok", "Instagram", "Dailymotion",
    "Twitch", "Reddit", "Twitter/X", "Facebook", "SoundCloud",
    "And 1000+ more sites"
]

def main(page: ft.Page):
    page.title = "Vibe Downloader Pro"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 700
    page.window_height = 850
    page.padding = 30
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    url_input = ft.TextField(label="Paste URL Here", hint_text="https://...", autofocus=True, width=600)
    
    # Restored Quality Settings
    quality_dropdown = ft.Dropdown(
        label="Select Quality",
        width=300,
        options=[
            ft.dropdown.Option("best", text="Best Quality (Highest)"),
            ft.dropdown.Option("1080", text="HD (1080p)"),
            ft.dropdown.Option("720", text="Standard (720p)"),
            ft.dropdown.Option("worst", text="Data Saver (Lowest)"),
        ],
        value="best"
    )

    progress_bar = ft.ProgressBar(width=600, color="blue", visible=False)
    status_text = ft.Text(value="Ready to vibe.", italic=True, color=ft.Colors.GREY_400)

    def progress_hook(d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%').replace('%','')
            try:
                progress_bar.value = float(p) / 100
                status_text.value = f"Downloading: {d.get('_percent_str')}"
            except: pass
        page.update()

    def run_download(mode):
        if not url_input.value:
            status_text.value = "Error: No URL provided."; page.update(); return
        
        q = quality_dropdown.value
        status_text.value = f"Starting {mode} download at {q} quality..."; progress_bar.visible = True; page.update()
        
        try:
            downloads_path = str(Path.home() / "Downloads")
            ydl_opts = {'outtmpl': f'{downloads_path}/%(title)s.%(ext)s', 'progress_hooks': [progress_hook], 'quiet': True}
            
            # Map quality selection to yt-dlp format strings
            format_str = "best"
            if q == "1080": format_str = "bestvideo[height<=1080]+bestaudio/best"
            elif q == "720": format_str = "bestvideo[height<=720]+bestaudio/best"
            elif q == "worst": format_str = "worst"

            if mode == "Audio":
                ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]})
            elif mode == "Playlist":
                ydl_opts.update({'format': format_str, 'noplaylist': False})
            else: # Video
                ydl_opts.update({'format': f'{format_str}/best', 'merge_output_format': 'mp4', 'noplaylist': True})

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url_input.value])
            status_text.value = "Success! Check your Downloads folder."; status_text.color = ft.Colors.GREEN_400
        except Exception as ex:
            status_text.value = f"Error: {str(ex)[:50]}..."; status_text.color = ft.Colors.RED_400
        finally:
            progress_bar.visible = False; page.update()

    def build_col(label, icon, mode):
        return ft.Column([
            ft.Icon(icon, size=40, color=ft.Colors.BLUE_400),
            ft.Text(label, weight="bold"),
            ft.ElevatedButton("DOWNLOAD", on_click=lambda _: run_download(mode))
        ], horizontal_alignment="center", spacing=10)

    def toggle_platforms(e):
        platforms_list.visible = not platforms_list.visible
        show_platforms_btn.text = "Hide Sites" if platforms_list.visible else "Show Supported Sites"
        page.update()
    
    show_platforms_btn = ft.Button("Show Supported Sites", on_click=toggle_platforms, width=250)
    platforms_list = ft.Column([ft.Text(f"• {p}", size=11, color=ft.Colors.GREY_300) for p in SUPPORTED_PLATFORMS], visible=False)

    page.add(
        ft.Column([
            ft.Text("Vibe Downloader Pro", size=36, weight="bold", color=ft.Colors.BLUE_200),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            url_input,
            quality_dropdown, # Added Quality Selector
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            ft.Row([
                build_col("AUDIO", ft.Icons.MUSIC_NOTE, "Audio"),
                build_col("VIDEO", ft.Icons.MOVIE, "Video"),
                build_col("PLAYLIST", ft.Icons.PLAYLIST_PLAY, "Playlist"),
            ], alignment="center", spacing=40),
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            progress_bar,
            status_text,
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            show_platforms_btn,
            platforms_list,
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            ft.Text("Version 1.0.0 - 04/30/2026", size=10, color=ft.Colors.GREY_600),
        ], horizontal_alignment="center")
    )

if __name__ == "__main__":
    ft.app(target=main)