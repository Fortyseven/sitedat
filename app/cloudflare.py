"""Cloudflare / WAF challenge detection and optional bypass helpers.

Separated to keep main script uncluttered.

Public functions:
- is_cloudflare_challenge(status_code: int, body: str) -> bool
- try_cloudflare_bypass(url: str, session_headers: dict, timeout: int = 30) -> tuple[bool, int, str]
  Returns (success, status_code, body). success True means challenge solved.
"""

from __future__ import annotations

from typing import Tuple


def is_cloudflare_challenge(status_code: int, body: str) -> bool:
    """Detect a Cloudflare (or similar) JS challenge page.

    We specifically look for typical markers that appear in challenge bodies.
    Keep this conservative to avoid false positives on generic 403 pages.
    """
    if status_code == 403 and (
        "cdn-cgi/challenge-platform" in body or "__CF$cv$params" in body
    ):
        return True
    return False


def try_cloudflare_bypass(
    url: str, session_headers: dict, timeout: int = 30
) -> Tuple[bool, int, str]:
    """Attempt to bypass a Cloudflare JS challenge using cloudscraper.

    Parameters
    ----------
    url : str
        Target URL to fetch after challenge detection.
    session_headers : dict
        Headers from the existing session to mimic continuity.
    timeout : int
        Request timeout in seconds.

    Returns
    -------
    success : bool
        True if bypass succeeded (no challenge detected and < 400 status).
    status_code : int
        HTTP status code from bypass attempt (or 0 on import failure).
    body : str
        Response body (may be empty if import failed or exception occurred).
    """
    try:
        import cloudscraper  # type: ignore
    except ImportError:
        return False, 0, ""

    try:
        scraper = cloudscraper.create_scraper()
        scraper.headers.update(session_headers)
        resp = scraper.get(url, timeout=timeout)
        body = resp.text
        if (
            not is_cloudflare_challenge(resp.status_code, body)
            and resp.status_code < 400
        ):
            return True, resp.status_code, body
        return False, resp.status_code, body
    except Exception:
        return False, 0, ""
