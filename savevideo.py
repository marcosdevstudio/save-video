#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn
import yt_dlp

console = Console()
stderr_console = Console(stderr=True)

SUPPORTED_HOSTS = (
    "youtube.com",
    "youtu.be",
    "instagram.com",
    "tiktok.com",
    "vm.tiktok.com",
)


def sanitize_title(title: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]", "", title)
    return cleaned.strip()[:180] or "download"


def is_supported_host(url: str) -> bool:
    lower = url.lower()
    return any(host in lower for host in SUPPORTED_HOSTS)


def resolve_ffmpeg_paths() -> tuple[str, str]:
    candidates = [
        os.environ.get("FFMPEG_BIN"),
        os.environ.get("FFMPEG_PATH"),
        os.environ.get("PATH", ""),
    ]

    paths: list[str] = []
    for candidate in candidates:
        if not candidate:
            continue
        paths.extend(candidate.split(os.pathsep))

    for directory in paths:
        if not directory:
            continue
        ffmpeg_path = Path(directory) / "ffmpeg.exe"
        ffprobe_path = Path(directory) / "ffprobe.exe"
        if ffmpeg_path.exists() and ffprobe_path.exists():
            return str(ffmpeg_path), str(ffprobe_path)

    default_dirs = [
        Path(r"C:\Users\Marcos\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin"),
        Path(r"C:\Program Files\FFmpeg\bin"),
        Path(r"C:\Program Files\Git\usr\bin"),
    ]

    for directory in default_dirs:
        ffmpeg_path = directory / "ffmpeg.exe"
        ffprobe_path = directory / "ffprobe.exe"
        if ffmpeg_path.exists() and ffprobe_path.exists():
            return str(ffmpeg_path), str(ffprobe_path)

    return "ffmpeg", "ffprobe"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Downloader de vídeo para YouTube, Instagram e TikTok com interface bonita.",
    )
    parser.add_argument("url", help="URL do vídeo, perfil ou playlist")
    parser.add_argument(
        "-o",
        "--output-dir",
        default="downloads",
        help="Diretório onde os arquivos serão salvos",
    )
    parser.add_argument(
        "-f",
        "--format",
        default="bestvideo+bestaudio/best",
        help="Formato do yt-dlp (ex.: best, bv*+ba/b)",
    )
    parser.add_argument(
        "--audio-only",
        action="store_true",
        help="Extrai apenas o áudio em MP3",
    )
    parser.add_argument(
        "--no-playlist",
        action="store_true",
        help="Baixa apenas o primeiro item da playlist",
    )
    parser.add_argument(
        "--no-watermark",
        action="store_true",
        help="Tenta baixar versões sem marca d'água quando o site oferecer",
    )
    parser.add_argument(
        "--cookie-file",
        default=None,
        help="Arquivo de cookies para sites que exigem login",
    )
    return parser


def get_ydl_options(
    output_dir: Path,
    format_string: str,
    audio_only: bool,
    no_playlist: bool,
    no_watermark: bool,
    cookie_file: str | None,
) -> dict:
    extractor_args: dict[str, list[str]] = {}
    if no_watermark:
        extractor_args = {"youtube": ["player_client=ios,web"], "tiktok": ["watermark=0"]}

    options: dict[str, object] = {
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
        "format": "bestaudio/best" if audio_only else format_string,
        "noplaylist": no_playlist,
        "quiet": False,
        "no_warnings": False,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "restrictfilenames": False,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        },
        "cookies": cookie_file,
        "extractor_args": extractor_args,
        "postprocessors": [],
    }

    if audio_only:
        options["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "0",
            }
        ]

    return options


def inspect_video(url: str, no_watermark: bool = False) -> dict:
    """Consulta os metadados e as alturas disponíveis sem iniciar o download."""
    ffmpeg_path, ffprobe_path = resolve_ffmpeg_paths()
    options = get_ydl_options(
        output_dir=Path("downloads"),
        format_string="bestvideo+bestaudio/best",
        audio_only=False,
        no_playlist=True,
        no_watermark=no_watermark,
        cookie_file=None,
    )
    options.update(
        {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "ffmpeg_location": str(Path(ffmpeg_path).parent),
            "ffprobe_location": str(Path(ffprobe_path).parent),
        }
    )

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)

    formats = info.get("formats") or []
    heights = sorted(
        {
            int(item["height"])
            for item in formats
            if item.get("height") and str(item["height"]).isdigit()
        },
        reverse=True,
    )
    return {
        "title": info.get("title") or "Vídeo sem título",
        "duration": info.get("duration"),
        "uploader": info.get("uploader") or info.get("channel") or "",
        "heights": heights,
    }


def download_video(
    url: str,
    output_dir: str,
    format_string: str,
    audio_only: bool,
    no_playlist: bool,
    no_watermark: bool,
    cookie_file: str | None,
) -> None:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    if not is_supported_host(url):
        console.print(
            "[yellow]Atenção:[/yellow] o site pode não ser suportado oficialmente; tente com YouTube, Instagram ou TikTok para melhor compatibilidade."
        )

    panel = Panel(
        f"URL: {url}\nDestino: {destination.resolve()}",
        title="SaveVideo",
        subtitle="download em execução",
        border_style="cyan",
    )
    console.print(panel)

    if no_watermark:
        console.print("[bold yellow]Tentando baixar em versão sem marca d'água quando disponível.[/bold yellow]")

    ffmpeg_path, ffprobe_path = resolve_ffmpeg_paths()

    ydl_options = get_ydl_options(
        output_dir=destination,
        format_string=format_string,
        audio_only=audio_only,
        no_playlist=no_playlist,
        no_watermark=no_watermark,
        cookie_file=cookie_file,
    )
    ydl_options["ffmpeg_location"] = str(Path(ffmpeg_path).parent)
    ydl_options["ffprobe_location"] = str(Path(ffprobe_path).parent)

    try:
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task("Baixando vídeo", total=100)

            class PatchedYoutubeDL(yt_dlp.YoutubeDL):
                def process_video_result(self, info, *, download):
                    if info.get("title"):
                        info["title"] = sanitize_title(info["title"])
                    return super().process_video_result(info, download=download)

            with PatchedYoutubeDL(ydl_options) as ydl:
                ydl.download([url])
            progress.update(task_id, completed=100)
    except Exception as exc:  # pragma: no cover - feedback ao usuário
        stderr_console.print(f"[bold red]Erro:[/bold red] {exc}")
        raise SystemExit(1) from exc

    console.print("[bold green]Download concluído![/bold green]")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    download_video(
        url=args.url,
        output_dir=args.output_dir,
        format_string=args.format,
        audio_only=args.audio_only,
        no_playlist=args.no_playlist,
        no_watermark=args.no_watermark,
        cookie_file=args.cookie_file,
    )


if __name__ == "__main__":
    main()
