from __future__ import annotations

import html
import re
import subprocess
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime

PRESS_LIST_URL = "https://www.nhsrcl.in/press-release.aspx"
PRESS_BASE = "https://www.nhsrcl.in/press-release"
USER_AGENT = "BulletTrainStation-DevSync/1.0 (+https://bullettrainstation.com)"


@dataclass(frozen=True)
class NhsrclPressItem:
    title: str
    published_on: date
    source_url: str


_CARD_RE = re.compile(
    r'<div class="card-date-badge">\s*(\d{2}-\d{2}-\d{4})\s*</div>\s*</div>\s*'
    r'<div class="card-content">\s*<h3 class="card-title">\s*(.*?)\s*</h3>',
    re.DOTALL | re.IGNORECASE,
)


def slugify_nhsrcl_press_title(title: str) -> str:
    normalized = (
        unicodedata.normalize("NFKD", title)
        .encode("ascii", "ignore")
        .decode("ascii")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("'", "")
        .replace("'", "")
        .lower()
    )
    slug = re.sub(r"[^a-z0-9\s-]", "", normalized).strip()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug


def nhsrcl_press_release_url(title: str) -> str:
    return f"{PRESS_BASE}/{slugify_nhsrcl_press_title(title)}"


def _fetch_html_curl(url: str, timeout: float) -> str:
    result = subprocess.run(
        ["curl", "-sL", "-A", USER_AGENT, "--max-time", str(int(timeout)), url],
        check=True,
        capture_output=True,
    )
    return result.stdout.decode("utf-8", errors="replace")


def _fetch_html(url: str, timeout: float = 30.0) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except urllib.error.URLError:
        return _fetch_html_curl(url, timeout)


def parse_press_listing(html_text: str) -> list[NhsrclPressItem]:
    items: list[NhsrclPressItem] = []
    for match in _CARD_RE.finditer(html_text):
        raw_date, raw_title = match.group(1), match.group(2)
        title = html.unescape(re.sub(r"\s+", " ", raw_title).strip())
        published = datetime.strptime(raw_date, "%d-%m-%Y").date()
        items.append(
            NhsrclPressItem(
                title=title,
                published_on=published,
                source_url=nhsrcl_press_release_url(title),
            )
        )
    return items


def fetch_latest_press_releases() -> list[NhsrclPressItem]:
    try:
        html_text = _fetch_html(PRESS_LIST_URL)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Could not load NHSRCL press listing: {exc}") from exc
    return parse_press_listing(html_text)


def default_summary(title: str, published_on: date) -> str:
    when = f"{published_on.day} {published_on.strftime('%B %Y')}"
    return (
        f"Official NHSRCL release ({when}): {title}. "
        "Unofficial one-line pointer — open the source link for the full brief."
    )