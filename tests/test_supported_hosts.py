from savevideo_cli import is_supported_host


def test_supported_hosts():
    assert is_supported_host("https://www.youtube.com/watch?v=abc") is True
    assert is_supported_host("https://youtu.be/abc") is True
    assert is_supported_host("https://www.instagram.com/reel/abc/") is True
    assert is_supported_host("https://www.tiktok.com/@user/video/123") is True


def test_unsupported_hosts():
    assert is_supported_host("https://example.com/video") is False
