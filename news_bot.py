"""
Олон ангилалт өглөөний мэдээний bot.
8 ангиллын RSS feed-ээс мэдээ татаж, англи мэдээг монгол руу орчуулаад,
шүүлтүүртэй нэг HTML хуудас болгож үүсгэнэ.
"""

import sys
import subprocess
import importlib
import html
import json
import time
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError

# Windows console-д кирилл үсэг гаргахын тулд UTF-8 болгоно
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


def ensure_package(pkg_name: str, import_name: str | None = None):
    """Шаардлагатай library байхгүй бол автоматаар суулгана."""
    name = import_name or pkg_name
    try:
        return importlib.import_module(name)
    except ImportError:
        print(f"[setup] '{pkg_name}' суулгаж байна...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", pkg_name]
        )
        return importlib.import_module(name)


feedparser = ensure_package("feedparser")
_dt = ensure_package("deep-translator", "deep_translator")
GoogleTranslator = _dt.GoogleTranslator
MyMemoryTranslator = _dt.MyMemoryTranslator


CATEGORIES = [
    {
        "key": "ai-tech",
        "name": "AI / Tech",
        "color": "#7aa2ff",
        "icon": "AI",
        "sources": [
            {"name": "Hacker News", "url": "https://news.ycombinator.com/rss"},
            {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
            {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml"},
            {
                "name": "Anthropic / Claude",
                "url": "https://news.google.com/rss/search?q=Anthropic+OR+%22Claude+AI%22&hl=en-US&gl=US&ceid=US:en",
            },
        ],
    },
    {
        "key": "business",
        "name": "Бизнес / Стартап",
        "color": "#10b981",
        "icon": "БИ",
        "sources": [
            {"name": "Bloomberg Business", "url": "https://feeds.bloomberg.com/business/news.rss"},
            {"name": "HN Startups", "url": "https://hnrss.org/newest?q=startup"},
            {"name": "Entrepreneur", "url": "https://feeds.feedburner.com/entrepreneur/latest"},
        ],
    },
    {
        "key": "finance",
        "name": "Финанс / Хөрөнгө оруулалт",
        "color": "#f59e0b",
        "icon": "ФИ",
        "sources": [
            {"name": "Bloomberg Markets", "url": "https://feeds.bloomberg.com/markets/news.rss"},
            {"name": "Financial Times", "url": "https://www.ft.com/rss/home"},
            {"name": "MarketWatch", "url": "https://feeds.marketwatch.com/marketwatch/topstories/"},
        ],
    },
    {
        "key": "world",
        "name": "Дэлхийн мэдээ",
        "color": "#3b82f6",
        "icon": "ДЭ",
        "sources": [
            {"name": "BBC World", "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
            {"name": "Reuters World", "url": "https://feeds.reuters.com/reuters/worldNews"},
            {"name": "CNN World", "url": "https://rss.cnn.com/rss/edition_world.rss"},
        ],
    },
    {
        "key": "health",
        "name": "Эрүүл мэнд",
        "color": "#ef4444",
        "icon": "ЭМ",
        "sources": [
            {"name": "WHO News", "url": "https://www.who.int/rss-feeds/news-english.xml"},
            {"name": "BBC Health", "url": "https://feeds.bbci.co.uk/news/health/rss.xml"},
            {"name": "Medical News Today", "url": "https://www.medicalnewstoday.com/newsfeeds/rss/medical_all.xml"},
        ],
    },
    {
        "key": "science",
        "name": "Шинжлэх ухаан",
        "color": "#a855f7",
        "icon": "ШУ",
        "sources": [
            {"name": "Science Daily", "url": "https://www.sciencedaily.com/rss/all.xml"},
            {"name": "Nature", "url": "https://feeds.nature.com/nature/rss/current"},
            {"name": "Scientific American", "url": "https://www.scientificamerican.com/feed/"},
        ],
    },
    {
        "key": "culture",
        "name": "Соёл / Дизайн / Арт",
        "color": "#ec4899",
        "icon": "СО",
        "sources": [
            {"name": "Designboom", "url": "https://www.designboom.com/feed/"},
            {"name": "Creative Bloq", "url": "https://www.creativebloq.com/feeds.xml"},
            {"name": "Dezeen", "url": "https://www.dezeen.com/feed/"},
        ],
    },
    {
        "key": "mongolia",
        "name": "Монголын мэдээ",
        "color": "#06b6d4",
        "icon": "МН",
        "sources": [
            {"name": "iKon.mn", "url": "https://ikon.mn/rss"},
            {"name": "Gogo.mn", "url": "https://gogo.mn/rss"},
            {"name": "News.mn", "url": "https://news.mn/feed"},
        ],
    },
    {
        "key": "crypto",
        "name": "Крипто арилжаа",
        "color": "#f7931a",
        "icon": "₿",
        "sources": [
            {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
            {"name": "Cointelegraph", "url": "https://cointelegraph.com/rss"},
            {"name": "Decrypt", "url": "https://decrypt.co/feed"},
            {"name": "Bitcoin Magazine", "url": "https://bitcoinmagazine.com/.rss/full/"},
        ],
    },
]


MARKET_SYMBOLS = [
    ("crypto",      "BTC-USD",   "Bitcoin (BTC/USD)"),
    ("crypto",      "ETH-USD",   "Ethereum (ETH/USD)"),
    ("crypto",      "SOL-USD",   "Solana (SOL/USD)"),
    ("indices",     "^GSPC",     "S&P 500"),
    ("indices",     "^IXIC",     "NASDAQ"),
    ("indices",     "^DJI",      "Dow Jones"),
    ("commodities", "GC=F",      "Алт (унц, USD)"),
    ("commodities", "CL=F",      "Газрын тос WTI (баррель)"),
    ("commodities", "SI=F",      "Мөнгө (унц, USD)"),
    ("forex",       "MNT=X",     "USD → MNT"),
    ("forex",       "EURMNT=X",  "EUR → MNT"),
    ("forex",       "JPYMNT=X",  "JPY → MNT"),
    ("forex",       "GBPMNT=X",  "GBP → MNT"),
]

MARKET_GROUPS = {
    "crypto":      {"title": "Крипто",   "icon": "₿",  "color": "#f7931a"},
    "indices":     {"title": "Индекс",   "icon": "📈", "color": "#7aa2ff"},
    "commodities": {"title": "Түүхий эд", "icon": "🛢", "color": "#f59e0b"},
    "forex":       {"title": "Форекс",   "icon": "💱", "color": "#10b981"},
}


MAX_ITEMS_PER_SOURCE = 10
OUTPUT_FILE = Path(__file__).parent / "news.html"
CACHE_FILE = Path(__file__).parent / "translations.json"
TARGET_LANG = "mn"

TRANSLATE_DELAY_SEC = 0.25
TRANSLATE_RETRIES = 3
TRANSLATE_BACKOFF_SEC = 8


def is_mongolian_source(url: str) -> bool:
    """URL домэйн .mn-ээр төгсвөл монгол гэж үзнэ (орчуулга алгасна)."""
    try:
        host = urlparse(url).netloc.lower()
        return host.endswith(".mn")
    except Exception:
        return False


def clean_summary(raw: str, limit: int = 280) -> str:
    """HTML tag-уудыг арилгаж, товч хэлбэрт оруулна."""
    import re

    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", "", raw)
    text = re.sub(r"\s+", " ", text).strip()
    text = html.unescape(text)
    if len(text) > limit:
        text = text[:limit].rstrip() + "…"
    return text


def format_date(entry) -> str:
    """RSS entry-ний огноог уншиж форматлана."""
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            try:
                dt = datetime(*t[:6], tzinfo=timezone.utc)
                return dt.strftime("%Y-%m-%d %H:%M UTC")
            except (TypeError, ValueError):
                continue
    return entry.get("published") or entry.get("updated") or ""


def fetch_source(source: dict) -> list[dict]:
    """Нэг RSS feed татна. Алдаатай эх сурвалжийг алгасаад хоосон жагсаалт буцаана."""
    url = source["url"]
    name = source["name"]
    is_mn = is_mongolian_source(url)
    try:
        parsed = feedparser.parse(url)
    except Exception as e:
        print(f"    ! {name}: татаж чадсангүй ({e})")
        return []

    if parsed.bozo and not parsed.entries:
        print(f"    ! {name}: feed уншигдсангүй ({parsed.bozo_exception})")
        return []

    items = []
    for entry in parsed.entries[:MAX_ITEMS_PER_SOURCE]:
        items.append(
            {
                "title": entry.get("title", "(гарчиг алга)").strip(),
                "link": entry.get("link", "#"),
                "summary": clean_summary(
                    entry.get("summary") or entry.get("description") or ""
                ),
                "date": format_date(entry),
                "source_name": name,
                "source_lang": "mn" if is_mn else "en",
            }
        )
    print(f"    + {name}: {len(items)} мэдээ")
    return items


def fetch_category(category: dict) -> list[dict]:
    """Нэг ангиллын бүх эх сурвалжаас мэдээ татаж нэгтгэнэ."""
    print(f"[fetch] {category['name']}")
    items = []
    for source in category["sources"]:
        items.extend(fetch_source(source))
    return items


def _fetch_yahoo_quote(symbol: str) -> dict | None:
    """Yahoo Finance v8 chart endpoint-с одоогийн үнэ, өмнөх хаалт татна."""
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        "?interval=1d&range=2d"
    )
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (URLError, TimeoutError, json.JSONDecodeError) as e:
        print(f"    ! {symbol}: {e}")
        return None

    result = data.get("chart", {}).get("result")
    if not result:
        return None
    meta = result[0].get("meta") or {}
    price = meta.get("regularMarketPrice")
    prev = meta.get("chartPreviousClose") or meta.get("previousClose")
    if price is None:
        return None
    change_pct = None
    if prev:
        try:
            change_pct = (price - prev) / prev * 100
        except ZeroDivisionError:
            change_pct = None
    return {
        "price": price,
        "prev": prev,
        "change_pct": change_pct,
        "currency": meta.get("currency", ""),
    }


def fetch_market_snapshot() -> dict:
    """Бүх symbol-уудын live үнийг татаад бүлэглэж буцаана."""
    print("[market] Live үнэ татаж байна...")
    snapshot = {key: [] for key in MARKET_GROUPS}
    for group, symbol, name in MARKET_SYMBOLS:
        q = _fetch_yahoo_quote(symbol)
        if q is None:
            continue
        snapshot[group].append(
            {
                "symbol": symbol,
                "name": name,
                "price": q["price"],
                "change_pct": q["change_pct"],
            }
        )
        time.sleep(0.15)
    fetched = sum(len(v) for v in snapshot.values())
    print(f"[market] {fetched}/{len(MARKET_SYMBOLS)} symbol амжилттай")
    return snapshot


def load_cache() -> dict:
    """translations.json-ыг уншиж кэшийг буцаана."""
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"[cache] translations.json уншиж чадсангүй ({e}) — хоосноор эхэллээ")
        return {}


def save_cache(cache: dict) -> None:
    CACHE_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _is_rate_limited(err: Exception) -> bool:
    msg = str(err).lower()
    return "too many requests" in msg or "429" in msg


def _translate_once(primary, fallback, text: str) -> str | None:
    """
    Эхлээд Google Translate. Rate limit гарвал нэг л удаа MyMemory-т шилжинэ.
    Аль аль нь бүтэлгүй бол алдаа raise хийнэ (дуудагч англиар үлдээнэ).
    Хурдтай fail-хэх нь чухал — Actions runner-ийн IP аль аль сервистэй нэн даруй
    блоклогдож болзошгүй тул удаан retry хийвэл workflow timeout-д ордог.
    """
    if not text:
        return ""
    truncated = text[:490]
    try:
        return primary.translate(truncated)
    except Exception as e:
        if not _is_rate_limited(e):
            raise
    return fallback.translate(truncated)


def translate_all(data: list[dict], cache: dict) -> tuple[int, int, int]:
    """
    Бүх мэдээний title + summary-г монгол руу орчуулна.
    - Монгол эх сурвалж (.mn) — орчуулахгүй, эхээр нь үлдээнэ.
    - Кэшэд байгаа мэдээ — дахин орчуулахгүй.
    - Google Translate rate limit-д хүрэхээс сэргийлж request хоорондоо
      богино delay + rate limit гарвал backoff retry хийнэ.
    Буцаах: (шинээр орчуулсан, бүтэлгүй, монгол алгассан).
    """
    all_items = [it for cat in data for it in cat["items"]]
    total = len(all_items)
    translator = GoogleTranslator(source="auto", target=TARGET_LANG)
    fallback = MyMemoryTranslator(source="en-GB", target="mn-MN")
    new_count = 0
    fail_count = 0
    mn_count = 0

    for i, it in enumerate(all_items, start=1):
        print(
            f"\r[translate] Орчуулж байна... {i}/{total}",
            end="",
            flush=True,
        )

        if it["source_lang"] == "mn":
            it["title_mn"] = it["title"]
            it["summary_mn"] = it["summary"]
            mn_count += 1
            continue

        link = it["link"]
        cached = cache.get(link)
        if cached:
            it["title_mn"] = cached.get("title") or it["title"]
            it["summary_mn"] = cached.get("summary") or it["summary"]
            continue

        try:
            title_mn = _translate_once(translator, fallback, it["title"]) or it["title"]
            time.sleep(TRANSLATE_DELAY_SEC)
            summary_mn = _translate_once(translator, fallback, it["summary"]) or it["summary"]
            time.sleep(TRANSLATE_DELAY_SEC)
            it["title_mn"] = title_mn
            it["summary_mn"] = summary_mn
            cache[link] = {"title": title_mn, "summary": summary_mn}
            new_count += 1
        except Exception as e:
            it["title_mn"] = it["title"]
            it["summary_mn"] = it["summary"]
            fail_count += 1
            print(f"\n  ! Орчуулга алдаа ({link[:60]}...): {e}")

    print()
    return new_count, fail_count, mn_count


def render_card(it: dict) -> str:
    """Нэг мэдээний карт. Монгол эх сурвалжийн хувьд англи мөрүүдийг харуулахгүй."""
    title_en = it["title"]
    summary_en = it.get("summary", "")
    title_mn = it.get("title_mn") or title_en
    summary_mn = it.get("summary_mn") or summary_en
    is_mn_source = it["source_lang"] == "mn"

    if is_mn_source:
        title_en_html = ""
        summary_en_html = ""
    else:
        title_en_html = (
            f'<p class="title-en">{html.escape(title_en)}</p>'
            if title_mn != title_en
            else ""
        )
        summary_en_html = (
            f'<p class="summary-en">{html.escape(summary_en)}</p>'
            if summary_en and summary_en != summary_mn
            else ""
        )
    summary_mn_html = (
        f'<p class="summary">{html.escape(summary_mn)}</p>' if summary_mn else ""
    )

    return f"""
            <article class="card">
              <h3><a href="{html.escape(it['link'])}" target="_blank" rel="noopener">{html.escape(title_mn)}</a></h3>
              {title_en_html}
              {summary_mn_html}
              {summary_en_html}
              <div class="meta">
                <span class="source-tag">{html.escape(it['source_name'])}</span>
                <span class="date">{html.escape(it['date'])}</span>
                <a class="read-more" href="{html.escape(it['link'])}" target="_blank" rel="noopener">Унших →</a>
              </div>
            </article>
            """


def _format_price(v: float, symbol: str) -> str:
    if v is None:
        return "—"
    if abs(v) >= 1000:
        return f"{v:,.2f}"
    if abs(v) >= 1:
        return f"{v:.2f}"
    return f"{v:.4f}"


def render_market_snapshot(snapshot: dict) -> str:
    if not snapshot or not any(snapshot.values()):
        return ""
    groups_html = []
    for key, meta in MARKET_GROUPS.items():
        items = snapshot.get(key) or []
        if not items:
            continue
        rows = []
        for it in items:
            pct = it["change_pct"]
            if pct is None:
                pct_cls, pct_html = "flat", "—"
            else:
                pct_cls = "up" if pct >= 0 else "down"
                arrow = "▲" if pct >= 0 else "▼"
                pct_html = f"{arrow} {abs(pct):.2f}%"
            rows.append(
                f'<div class="market-row">'
                f'  <span class="market-name">{html.escape(it["name"])}</span>'
                f'  <span class="market-price">{_format_price(it["price"], it["symbol"])}</span>'
                f'  <span class="market-pct {pct_cls}">{pct_html}</span>'
                f'</div>'
            )
        groups_html.append(
            f'<div class="market-group" style="--mc: {meta["color"]}">'
            f'  <h3><span class="market-icon">{meta["icon"]}</span> {meta["title"]}</h3>'
            f'  <div class="market-body">{"".join(rows)}</div>'
            f'</div>'
        )
    return (
        '<section class="market-snapshot">'
        '  <h2 class="market-heading">📊 Арилжааны Snapshot</h2>'
        f' <div class="market-grid">{"".join(groups_html)}</div>'
        '</section>'
    )


def render_html(data: list[dict], market: dict | None = None) -> str:
    today = datetime.now().strftime("%Y оны %m сарын %d, %A")
    total = sum(len(cat["items"]) for cat in data)
    market_html = render_market_snapshot(market or {})

    # Шүүлтүүрийн товчнууд
    filter_buttons = [
        f'<button class="filter-btn active" data-filter="all">'
        f'<span class="nav-icon all-icon">★</span> Бүгд '
        f'<span class="count">{total}</span></button>'
    ]
    for cat_data in data:
        cat = cat_data["category"]
        cnt = len(cat_data["items"])
        filter_buttons.append(
            f'<button class="filter-btn" data-filter="{cat["key"]}" style="--c: {cat["color"]}">'
            f'<span class="nav-icon">{cat["icon"]}</span> {html.escape(cat["name"])} '
            f'<span class="count">{cnt}</span></button>'
        )

    # Ангилал бүрийн хэсэг
    sections = []
    for cat_data in data:
        cat = cat_data["category"]
        items = cat_data["items"]
        cards = "\n".join(render_card(it) for it in items)
        source_names = ", ".join(s["name"] for s in cat["sources"])
        sections.append(
            f"""
            <section data-category="{cat['key']}" class="source" style="--accent: {cat['color']}">
              <header class="source-head">
                <div class="source-icon">{cat['icon']}</div>
                <div>
                  <h2>{html.escape(cat['name'])}</h2>
                  <p class="source-url">{html.escape(source_names)}</p>
                </div>
                <div class="badge">{len(items)} мэдээ</div>
              </header>
              <div class="grid">
                {cards if items else '<p class="empty">Мэдээ татаж чадсангүй.</p>'}
              </div>
            </section>
            """
        )

    return f"""<!DOCTYPE html>
<html lang="mn">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>Өглөөний мэдээ — {today}</title>

<!-- PWA manifest + theme -->
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#0b0d12">

<!-- iOS / Safari standalone-д зориулсан tag-ууд -->
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Мэдээ">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" type="image/png" sizes="192x192" href="icon-192.png">
<link rel="icon" type="image/png" sizes="512x512" href="icon-512.png">

<style>
  :root {{
    --bg: #0b0d12;
    --panel: #131722;
    --border: #1f2533;
    --text: #e6e8ee;
    --muted: #8a92a6;
    --link: #7aa2ff;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ overflow-x: hidden; }}
  body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
    /* iPhone notch / safe area */
    padding-top: env(safe-area-inset-top);
    padding-left: env(safe-area-inset-left);
    padding-right: env(safe-area-inset-right);
    padding-bottom: env(safe-area-inset-bottom);
  }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px 80px; }}
  header.top {{
    padding-bottom: 24px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 32px;
    position: sticky;
    top: 0;
    background: linear-gradient(180deg, var(--bg) 80%, transparent);
    z-index: 10;
  }}
  header.top h1 {{
    font-size: clamp(28px, 4vw, 44px);
    margin: 0 0 8px;
    background: linear-gradient(90deg, #7aa2ff, #10b981, #f59e0b, #ec4899);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
  }}
  header.top p {{ color: var(--muted); margin: 0; }}
  .filters {{
    display: flex; flex-wrap: wrap; gap: 8px;
    margin: 20px 0 4px;
  }}
  .filter-btn {{
    display: inline-flex; align-items: center; gap: 8px;
    padding: 8px 14px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 999px;
    color: var(--text);
    font-size: 14px;
    cursor: pointer;
    font-family: inherit;
    transition: all .15s ease;
  }}
  .filter-btn:hover {{
    border-color: var(--c, var(--link));
    transform: translateY(-1px);
  }}
  .filter-btn.active {{
    border-color: var(--c, var(--link));
    background: rgba(255,255,255,.06);
  }}
  .nav-icon {{
    width: 22px; height: 22px; border-radius: 6px;
    background: var(--c, var(--link)); color: #fff;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700;
  }}
  .all-icon {{
    background: linear-gradient(135deg, #7aa2ff, #ec4899);
    font-size: 12px;
  }}
  .count {{
    background: rgba(255,255,255,.08);
    padding: 1px 8px; border-radius: 999px;
    font-size: 12px; color: var(--muted);
  }}
  .source {{
    margin-top: 56px;
    scroll-margin-top: 20px;
  }}
  .source.hidden {{ display: none; }}
  .source-head {{
    display: flex; align-items: center; gap: 16px;
    padding-bottom: 16px;
    border-bottom: 2px solid var(--accent);
    margin-bottom: 24px;
  }}
  .source-icon {{
    width: 48px; height: 48px; border-radius: 12px;
    background: var(--accent); color: #fff;
    display: inline-flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 16px;
    flex-shrink: 0;
  }}
  .source-head h2 {{ margin: 0; font-size: 22px; }}
  .source-url {{ margin: 2px 0 0; color: var(--muted); font-size: 12px; }}
  .badge {{
    margin-left: auto;
    background: var(--panel);
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 4px 12px; border-radius: 999px;
    font-size: 13px;
    flex-shrink: 0;
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 16px;
  }}
  .card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px 20px;
    transition: all .15s ease;
    display: flex; flex-direction: column;
  }}
  .card:hover {{
    border-color: var(--accent);
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(0,0,0,.3);
  }}
  .card h3 {{
    margin: 0 0 10px;
    font-size: 16px;
    line-height: 1.35;
  }}
  .card h3 a {{
    color: var(--text);
    text-decoration: none;
  }}
  .card h3 a:hover {{ color: var(--link); }}
  .title-en {{
    margin: -4px 0 12px;
    font-size: 12px;
    color: var(--muted);
    font-style: italic;
    line-height: 1.4;
  }}
  .summary {{
    color: var(--text);
    font-size: 14px;
    margin: 0 0 10px;
  }}
  .summary-en {{
    color: var(--muted);
    font-size: 12px;
    font-style: italic;
    margin: 0 0 14px;
    padding-left: 10px;
    border-left: 2px solid var(--border);
    line-height: 1.5;
    flex-grow: 1;
  }}
  .meta {{
    display: flex; align-items: center; justify-content: space-between;
    gap: 8px; flex-wrap: wrap;
    font-size: 12px;
    border-top: 1px solid var(--border);
    padding-top: 10px;
    margin-top: auto;
  }}
  .source-tag {{
    background: rgba(255,255,255,.06);
    color: var(--muted);
    padding: 2px 8px; border-radius: 999px;
    font-size: 11px;
  }}
  .date {{ color: var(--muted); font-size: 11px; }}
  .read-more {{
    color: var(--accent);
    text-decoration: none;
    font-weight: 600;
    margin-left: auto;
  }}
  .read-more:hover {{ text-decoration: underline; }}
  .empty {{ color: var(--muted); font-style: italic; }}
  footer {{
    margin-top: 64px; padding-top: 24px;
    border-top: 1px solid var(--border);
    text-align: center; color: var(--muted); font-size: 13px;
  }}

  /* === Арилжааны Snapshot === */
  .market-snapshot {{
    margin: 8px 0 32px;
    padding: 20px 22px 22px;
    background: linear-gradient(180deg, rgba(122,162,255,.05), rgba(236,72,153,.03));
    border: 1px solid var(--border);
    border-radius: 16px;
  }}
  .market-heading {{
    margin: 0 0 16px;
    font-size: 18px;
    color: var(--text);
  }}
  .market-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 16px;
  }}
  .market-group {{
    background: rgba(0,0,0,.2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 16px;
    border-top: 3px solid var(--mc);
  }}
  .market-group h3 {{
    margin: 0 0 10px;
    font-size: 14px;
    display: flex; align-items: center; gap: 8px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: .5px;
  }}
  .market-icon {{ font-size: 16px; }}
  .market-row {{
    display: grid;
    grid-template-columns: 1fr auto auto;
    gap: 10px;
    align-items: baseline;
    padding: 6px 0;
    border-bottom: 1px dashed rgba(255,255,255,.05);
    font-size: 13px;
  }}
  .market-row:last-child {{ border-bottom: none; }}
  .market-name {{ color: var(--text); }}
  .market-price {{
    font-variant-numeric: tabular-nums;
    font-weight: 600;
    color: var(--text);
  }}
  .market-pct {{
    font-variant-numeric: tabular-nums;
    font-size: 12px;
    font-weight: 600;
    min-width: 70px;
    text-align: right;
  }}
  .market-pct.up   {{ color: #10b981; }}
  .market-pct.down {{ color: #ef4444; }}
  .market-pct.flat {{ color: var(--muted); }}

  /* === Mobile-first responsive === */
  @media (max-width: 768px) {{
    .container {{ padding: 16px 14px 60px; }}
    header.top {{
      padding-bottom: 12px;
      margin-bottom: 20px;
    }}
    header.top h1 {{ font-size: 26px; }}
    header.top p {{ font-size: 13px; }}
    .filters {{
      /* Хэвтээ scroll — утсан дээр товчнууд олон үед ашигтай */
      flex-wrap: nowrap;
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
      scrollbar-width: none;
      margin: 14px -14px 0;
      padding: 0 14px 8px;
    }}
    .filters::-webkit-scrollbar {{ display: none; }}
    .filter-btn {{
      flex-shrink: 0;
      padding: 10px 14px;
      font-size: 14px;
    }}
    .source {{ margin-top: 36px; }}
    .source-head {{ gap: 12px; }}
    .source-head h2 {{ font-size: 18px; }}
    .source-icon {{
      width: 40px; height: 40px;
      font-size: 13px;
      border-radius: 10px;
    }}
    .source-url {{ font-size: 11px; }}
    .badge {{ font-size: 11px; padding: 3px 10px; }}
    .grid {{
      grid-template-columns: 1fr;
      gap: 12px;
    }}
    .card {{ padding: 16px 16px; }}
    .card h3 {{ font-size: 15px; }}
    .title-en {{ font-size: 11px; }}
    .summary {{ font-size: 13.5px; }}
    .summary-en {{ font-size: 11px; }}
    .meta {{ font-size: 11px; }}
  }}
</style>
</head>
<body>
  <div class="container">
    <header class="top">
      <h1>Өглөөний мэдээ</h1>
      <p>{today} · Нийт {total} мэдээ · {len(data)} ангилал</p>
      <div class="filters">
        {''.join(filter_buttons)}
      </div>
    </header>

    {market_html}

    {''.join(sections)}

    <footer>
      Үүсгэсэн: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ·
      Олон ангилалт мэдээний bot
    </footer>
  </div>
  <script>
    // Ангиллын шүүлтүүр
    document.querySelectorAll('.filter-btn').forEach(btn => {{
      btn.addEventListener('click', () => {{
        const key = btn.dataset.filter;
        document.querySelectorAll('.filter-btn').forEach(b => {{
          b.classList.toggle('active', b === btn);
        }});
        document.querySelectorAll('section[data-category]').forEach(sec => {{
          sec.classList.toggle('hidden', key !== 'all' && sec.dataset.category !== key);
        }});
        window.scrollTo({{ top: 0, behavior: 'smooth' }});
      }});
    }});

    // PWA service worker — offline-д ажиллах + автомат шинэчлэлт
    if ('serviceWorker' in navigator) {{
      window.addEventListener('load', () => {{
        navigator.serviceWorker
          .register('./service-worker.js')
          .catch(err => console.error('SW registration failed:', err));
      }});
    }}
  </script>
</body>
</html>
"""


def main():
    start = datetime.now()
    print(f"=== Олон ангилалт мэдээний bot — {start.strftime('%Y-%m-%d %H:%M')} ===")
    total_sources = sum(len(c["sources"]) for c in CATEGORIES)
    print(
        f"[plan] {len(CATEGORIES)} ангилал · {total_sources} эх сурвалж · "
        f"эх сурвалж тус бүрээс {MAX_ITEMS_PER_SOURCE} мэдээ хүртэл"
    )
    print("[note] Анх удаа / олон шинэ мэдээтэй үед 3–5 минут болж магадгүй.\n")

    data = []
    for category in CATEGORIES:
        items = fetch_category(category)
        data.append({"category": category, "items": items})

    cache = load_cache()
    print(f"\n[cache] {len(cache)} орчуулга кэшэд байна")

    try:
        new_count, fail_count, mn_count = translate_all(data, cache)
        print(
            f"[translate] Шинээр: {new_count} · Бүтэлгүй: {fail_count} · "
            f"Монгол (алгассан): {mn_count}"
        )
    finally:
        save_cache(cache)
        print(f"[cache] Хадгалсан: {CACHE_FILE.name} ({len(cache)} мэдээ)")

    market = fetch_market_snapshot()

    print("\n[render] HTML файл үүсгэж байна...")
    output = render_html(data, market)
    OUTPUT_FILE.write_text(output, encoding="utf-8")
    elapsed = (datetime.now() - start).total_seconds()
    print(f"[done] Үүсгэгдсэн: {OUTPUT_FILE}")
    print(f"[time] Нийт {elapsed:.1f} секунд зарцуулсан")

    if "--open" in sys.argv:
        webbrowser.open(OUTPUT_FILE.as_uri())
        print("[open] Browser-т нээлээ.")


if __name__ == "__main__":
    main()
