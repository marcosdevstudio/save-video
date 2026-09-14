#!/usr/bin/env python3
from __future__ import annotations

from savevideo import (
    build_parser,
    download_video,
    get_ydl_options,
    is_supported_host,
    main,
    sanitize_title,
)

__all__ = [
    "build_parser",
    "download_video",
    "get_ydl_options",
    "is_supported_host",
    "main",
    "sanitize_title",
]


if __name__ == "__main__":
    main()
