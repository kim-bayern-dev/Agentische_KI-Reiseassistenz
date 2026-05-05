import re
import html
from urllib.parse import urlparse

MARKER_RE = re.compile(r"\[\[\s*(?P<key>[^:\]]+?)\s*:\s*(?P<value>.*?)\s*\]\]")


def _normalize_url(u: str) -> str:
    u = u.strip()
    if u and "://" not in u:
        u = "https://" + u
    return u


def _looks_like_url(v: str) -> bool:
    v = v.strip()
    return bool(
        re.match(r"(?i)^https?://", v)
        or v.startswith("www.")
        or re.match(r"(?i)^[\w.-]+\.[a-z]{2,}([/:?#]|$)", v)
    )


def _base_domain(u: str) -> str:
    u = _normalize_url(u)
    netloc = urlparse(u).netloc or u
    netloc = netloc.split("@")[-1].split(":")[0]
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc or "link"


def inject_source_chips(text: str) -> str:
    def repl(m: re.Match) -> str:
        key = m.group("key").strip()
        key_l = key.lower()
        value = m.group("value").strip()

        if key_l == "tournr":
            nr = value.zfill(2) if value.isdigit() else value
            nr_txt = html.escape(nr)
            tip = html.escape(f"Aus der Tour {nr}", quote=True)
            return f'<span class="src-chip" data-tip="{tip}">📒 {nr_txt}</span>'
        elif key_l == "weather":
            query = value.zfill(2) if value.isdigit() else value
            query_txt = html.escape(query)
            tip = html.escape(f"Aus dem Wetterbericht für {query}", quote=True)
            return f'<span class="src-chip" data-tip="{tip}">⛅ Wetter</span>'

        if _looks_like_url(value):
            url = _normalize_url(value)
            label = html.escape(_base_domain(url))
            url_attr = html.escape(url, quote=True)
            tip = html.escape(url, quote=True)
            return (
                f'<a class="src-chip" href="{url_attr}" target="_blank" rel="noopener noreferrer" '
                f'data-tip="{tip}">🔎 {label}</a>'
            )

        # fallback
        k = html.escape(key)
        tip = html.escape(value, quote=True)
        return f'<span class="src-chip" data-tip="{tip}">{k}</span>'

    if text is None:
        return text
    return MARKER_RE.sub(repl, text)
