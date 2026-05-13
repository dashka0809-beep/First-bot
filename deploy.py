"""
GitHub Pages-т deploy хийхэд бэлтгэх скрипт.

Ажиллах дараалал:
  1. news_bot.py-ийг ажиллуулна (шинэ мэдээ татаж news.html үүсгэнэ).
  2. Icon (192/512/180) байхгүй бол PIL-ээр зурж үүсгэнэ.
  3. docs/ фолдер үүсгээд PWA-д шаардлагатай бүх файлуудыг тэнд хуулна.

Дараа нь GitHub Desktop-аар push хийгээд GitHub Pages-ийг
Settings > Pages > Source: main branch / docs folder болгож идэвхжүүлнэ.
"""

import importlib
import shutil
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


def ensure_package(pkg_name: str, import_name: str | None = None):
    name = import_name or pkg_name
    try:
        return importlib.import_module(name)
    except ImportError:
        print(f"[setup] '{pkg_name}' суулгаж байна...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", pkg_name]
        )
        return importlib.import_module(name)


# Pillow зөвхөн icon үүсгэхэд хэрэгтэй
ensure_package("Pillow", "PIL")
from PIL import Image, ImageDraw, ImageFont  # noqa: E402


ROOT = Path(__file__).parent
DOCS = ROOT / "docs"

# Брэндийн өнгөнүүд (HTML дотрох градиенттэй адил)
COLOR_TOP = (122, 162, 255)   # #7aa2ff
COLOR_BOTTOM = (236, 72, 153) # #ec4899
COLOR_TEXT = (255, 255, 255)


def draw_gradient(size: int) -> Image.Image:
    """Босоо градиенттэй RGB зураг үүсгэнэ (хурдан, мөр тус бүрээр)."""
    img = Image.new("RGB", (size, size))
    draw = ImageDraw.Draw(img)
    for y in range(size):
        t = y / (size - 1)
        color = tuple(
            int(COLOR_TOP[i] + (COLOR_BOTTOM[i] - COLOR_TOP[i]) * t) for i in range(3)
        )
        draw.line([(0, y), (size, y)], fill=color)
    return img


def find_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Windows / macOS / Linux дээрх нийтлэг тод font-ыг хайна."""
    candidates = [
        "arialbd.ttf",
        "Arial Bold.ttf",
        "seguibl.ttf",  # Segoe UI Black
        "SegoeUIB.ttf",
        "segoeuib.ttf",
        "Helvetica.ttc",
        "DejaVuSans-Bold.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    print("  ! Тод font олдсонгүй, default PIL font ашиглана")
    return ImageFont.load_default()


def generate_icon(size: int, output_path: Path, *, force: bool = False) -> None:
    """Bөөрөнхий булантай градиент дэвсгэр + цагаан 'M' үсэгтэй icon."""
    if output_path.exists() and not force:
        print(f"  · {output_path.name} аль хэдийн байна, алгаслаа")
        return

    gradient = draw_gradient(size).convert("RGBA")

    # Bөөрөнхий булан
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [(0, 0), (size - 1, size - 1)],
        radius=int(size * 0.22),
        fill=255,
    )

    icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    icon.paste(gradient, (0, 0), mask)

    # "M" үсэг — голд
    draw = ImageDraw.Draw(icon)
    font = find_font(int(size * 0.6))
    text = "M"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - text_w) // 2 - bbox[0]
    y = (size - text_h) // 2 - bbox[1] - int(size * 0.02)
    draw.text((x, y), text, fill=COLOR_TEXT + (255,), font=font)

    icon.save(output_path, "PNG", optimize=True)
    print(f"  + {output_path.name} ({size}×{size})")


def run_news_bot() -> None:
    """news_bot.py-ийг ажиллуулж news.html шинэчилнэ."""
    print("[1/4] news_bot.py ажиллуулж байна (3–5 минут болж магадгүй)...")
    subprocess.check_call([sys.executable, str(ROOT / "news_bot.py")])


def ensure_icons() -> None:
    """3 хэмжээний icon шалгаж, байхгүй бол үүсгэнэ."""
    print("\n[2/4] Icon үүсгэж байна...")
    for size, name in [(192, "icon-192.png"), (512, "icon-512.png"), (180, "icon-180.png")]:
        generate_icon(size, ROOT / name)


def build_docs() -> None:
    """docs/ фолдерт PWA-д шаардлагатай бүх файлыг хуулна."""
    print("\n[3/4] docs/ фолдер бэлдэж байна...")
    DOCS.mkdir(exist_ok=True)

    # news.html → docs/index.html (GitHub Pages-ийн default хуудас)
    src_html = ROOT / "news.html"
    if not src_html.exists():
        raise FileNotFoundError(
            "news.html олдсонгүй. Эхлээд news_bot.py-ийг ажиллуулна уу."
        )
    shutil.copy2(src_html, DOCS / "index.html")
    print(f"  + index.html (← news.html)")

    # PWA нэмэлт файлууд
    extras = ["manifest.json", "service-worker.js", "icon-192.png", "icon-512.png", "icon-180.png"]
    for name in extras:
        src = ROOT / name
        if not src.exists():
            print(f"  ! {name} олдсонгүй, алгаслаа")
            continue
        shutil.copy2(src, DOCS / name)
        print(f"  + {name}")


def report() -> None:
    """Эцсийн тайлан."""
    print("\n[4/4] Бэлэн!")
    total = 0
    for f in sorted(DOCS.iterdir()):
        size_kb = f.stat().st_size / 1024
        total += size_kb
        print(f"  - {f.name:30s} {size_kb:>8.1f} KB")
    print(f"  {'─' * 42}")
    print(f"  {'Нийт':30s} {total:>8.1f} KB")
    print("\nДараагийн алхам:")
    print("  1. GitHub Desktop-аар commit + push хийнэ")
    print("  2. GitHub > Settings > Pages > main / docs идэвхжүүлнэ")
    print("  3. https://USERNAME.github.io/REPO/ URL-аар нээнэ")


def main():
    args = sys.argv[1:]
    skip_fetch = "--no-fetch" in args or "--skip-fetch" in args

    if skip_fetch:
        print("[1/4] news_bot.py-ийг алгаслаа (--no-fetch)")
    else:
        run_news_bot()

    ensure_icons()
    build_docs()
    report()


if __name__ == "__main__":
    main()
