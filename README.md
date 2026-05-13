# Олон ангилалт өглөөний мэдээний bot — PWA

RSS feed-ээс **8 ангиллын** мэдээ татаж, англи мэдээг **монгол хэл рүү автоматаар орчуулаад**, **шүүлтүүртэй PWA** болгож үүсгэдэг хувийн bot. GitHub Pages-т байршуулж утсан дээр бүтэн дэлгэцээр унших боломжтой.

## Ангилалууд

| Ангилал | Өнгө | Эх сурвалжууд |
|---------|------|---------------|
| **AI / Tech** | Цэнхэр | Hacker News · TechCrunch · The Verge · Anthropic / Claude |
| **Бизнес / Стартап** | Ногоон | Bloomberg Business · HN Startups · Entrepreneur |
| **Финанс / Хөрөнгө оруулалт** | Алтан шар | Bloomberg Markets · Financial Times · MarketWatch |
| **Дэлхийн мэдээ** | Цэнхэр | BBC World · Reuters World · CNN World |
| **Эрүүл мэнд** | Улаан | WHO · BBC Health · Medical News Today |
| **Шинжлэх ухаан** | Ягаан | Science Daily · Nature · Scientific American |
| **Соёл / Дизайн / Арт** | Ягаан-улаан | Designboom · Creative Bloq · Dezeen |
| **Монголын мэдээ** | Ногоон-цэнхэр | iKon.mn · Gogo.mn · News.mn |

## Юу хийдэг вэ

1. Дээрх 24 RSS эх сурвалжаас тус бүрээс хамгийн ихдээ 10 мэдээ татна (~150–200 мэдээ).
2. Англи мэдээний гарчиг + товч агуулгыг Google Translate-ээр монгол руу орчуулна.
3. **Монгол эх сурвалжийн** (.mn домэйнтэй) мэдээг орчуулахгүй — эхээр нь үлдээнэ.
4. **PWA** (Progressive Web App) болгож, утсан дээр Home Screen-д нэмэх боломжтой нэг HTML файл болгож гаргана.

## PWA онцлог

- **Утсан дээр app шиг ажиллана** — Home Screen-д нэмэхэд бүтэн дэлгэцээр (бараг native app шиг) нээгдэнэ
- **Офлайнд ажиллана** — service worker сүүлийн харсан хувилбарыг кэшэлдэг тул интернетгүй үед ч уншиж болно
- **Автоматаар шинэчлэгдэнэ** — онлайн үед хамгийн шинэ хувилбар татна
- **Утсанд тохирсон дизайн** — карт нэг баганаар, шүүлтүүрийн товч хэвтээ scroll-той, iPhone-ийн notch (safe area) дэмжсэн

## Файлуудын бүтэц

```
news-bot/
├── news_bot.py            # Мэдээ татах + орчуулах + HTML үүсгэх гол скрипт
├── deploy.py              # docs/ фолдер бэлдэх скрипт (PWA для GitHub Pages)
├── manifest.json          # PWA manifest (нэр, icon, өнгө)
├── service-worker.js      # Офлайн cache strategy
├── icon-192.png           # Android / Chrome icon
├── icon-512.png           # Том PWA icon (splash screen)
├── icon-180.png           # iOS Home Screen icon
├── news.html              # Локалаар ажиллуулсны үр дүн (Browser-т харна)
├── translations.json      # Орчуулгын кэш (git-д орохгүй)
├── README.md              # Энэ файл
├── .gitignore
└── docs/                  # GitHub Pages-т deploy хийх файлууд
    ├── index.html         # ← news.html-ийн хуулбар
    ├── manifest.json
    ├── service-worker.js
    └── icon-*.png
```

## Шаардлага

- **Python 3.14** (өөр 3.10+ ч ажиллана)
- Интернет холболт
- Library-ууд (автоматаар суулгана): `feedparser`, `deep-translator`, `Pillow` (icon үүсгэхэд)

## Локалаар ашиглах

**Зөвхөн news.html шинэчлэх (browser-т харах):**
```powershell
cd C:\Users\PC\Documents\news-bot
py -3.14 news_bot.py
```

**Browser-т шууд нээх:**
```powershell
py -3.14 news_bot.py --open
```

### Ажиллах хугацаа

- **Анх удаа** (кэш хоосон): **3–5 минут** — ~150+ мэдээ орчуулна
- **Өдөр бүр** (кэш дүүрэн): **30 секунд – 2 минут** — зөвхөн шинэ мэдээ орчуулагдана

---

## GitHub Pages-т deploy хийх

### Анх удаа: репо үүсгэж upload хийх

**1. GitHub-д шинэ repository үүсгэ**
   - https://github.com/new руу ор
   - Repository name: жишээ нь `morning-news` (хүссэн нэр)
   - **Private эсвэл Public** аль нь ч болно. GitHub Pages нь public free, private бол GitHub Pro хэрэгтэй
   - `Add README` чек **БҮҮ** тавь (бид өөрсдөө README-тэй)
   - Create repository товч дар

**2. GitHub Desktop ашиглан upload хий**
   - GitHub Desktop нээж File > Add local repository
   - `C:\Users\PC\Documents\news-bot` фолдерийг сонго
   - "Create a repository" эсвэл "Initialize git repository" сонголтыг сонгох
   - Эхний commit бичээд "Commit to main" дар
   - Дараа нь "Publish repository" товч дарж, дээр үүсгэсэн repo руу хол

**3. docs/ фолдер үүсгэх (deploy.py ажиллуулах)**
   ```powershell
   cd C:\Users\PC\Documents\news-bot
   py -3.14 deploy.py
   ```
   Энэ нь:
   - news_bot.py-ийг ажиллуулна (шинэ мэдээ татна)
   - Icon-уудыг үүсгэнэ (хэрвээ байхгүй бол)
   - `docs/` фолдерт PWA-д шаардлагатай бүх файлыг хуулна

   Хэрэв news.html аль хэдийн шинэ бөгөөд зөвхөн docs/ дахин бэлдэх бол:
   ```powershell
   py -3.14 deploy.py --no-fetch
   ```

**4. docs/-ийг GitHub-д push хий**
   - GitHub Desktop-д шинэ файлууд (docs/...) гарч ирнэ
   - Commit бичээд (жишээ нь "Deploy initial PWA") "Commit to main" дар
   - "Push origin" товч дарна

**5. GitHub Pages идэвхжүүлэх**
   - GitHub repository-гоо open хийнэ
   - **Settings > Pages** хэсэг рүү ор
   - **Source:** "Deploy from a branch"
   - **Branch:** `main` сонго, фолдер **`/docs`** сонго
   - **Save** товч дар
   - 1–2 минутын дараа репогийн дээд хэсэгт сайтын URL гарч ирнэ:
     ```
     https://USERNAME.github.io/REPO-NAME/
     ```

### Өдөр бүрийн шинэчлэлт

```powershell
cd C:\Users\PC\Documents\news-bot
py -3.14 deploy.py
```

Дараа нь GitHub Desktop-ыг нээгээд:
1. Шинэчлэгдсэн файлуудыг харна (`docs/index.html`)
2. Commit мессеж бичээд "Commit to main" дар
3. "Push origin" дар

1–2 минутын дараа URL дээр шинэ мэдээ гарч ирнэ.

---

## iPhone-оос Home Screen дээр нэмэх

1. **Safari** дээр URL-аа нээ: `https://USERNAME.github.io/REPO-NAME/`
2. Доод хэсгийн **Share** товч (дөрвөлжин дотор дээш сум) дар
3. Гарч ирсэн жагсаалтаас доош skrol хийгээд **"Add to Home Screen"** сонго
4. Нэр өг (default нь "Мэдээ"), баруун дээд буланд **"Add"** дар
5. Home Screen дээр "M" логотой icon гарч ирнэ
   - Энэ дээр товшиход бүтэн дэлгэцээр (Safari address bar-гүйгээр) нээгдэнэ
   - Офлайн үед ч хамгийн сүүлийн харсан хувилбар нь ажиллана

> **Анхаар:** Зөвхөн **Safari** дээр "Add to Home Screen" ажиллана. Chrome / Firefox дээр iOS-д энэ feature байхгүй.

---

## Орчуулга хэрхэн ажилладаг

- **Library:** [`deep-translator`](https://pypi.org/project/deep-translator/) — Google Translate-ийн үнэгүй wrapper. **API key хэрэггүй**.
- **Кэш:** `translations.json` файлд URL-ыг түлхүүр болгож хадгална. Дараагийн удаа татах үед дахин орчуулахгүй.
- **Хэлний автомат таних:** `.mn` домэйнтэй эх сурвалжийг монгол гэж үзэж орчуулга алгасна.
- **Алдаа гарвал:**
  - Орчуулга бүтэлгүй → мэдээ англиараа үлдэнэ, кэшэд орохгүй (дараа дахин оролдоно)
  - RSS feed татагдсангүй → тухайн эх сурвалжийг алгасна, бусад нь ажиллана

## Тохиргоо өөрчлөх

`news_bot.py` дотроос:

- **Мэдээний тоо:** `MAX_ITEMS_PER_SOURCE = 10`
- **Шинэ ангилал:** `CATEGORIES` жагсаалтад dict нэмэх (`key`, `name`, `color`, `icon`, `sources`)
- **Орчуулгын хэл:** `TARGET_LANG = "mn"`
- **Монгол гэж тооцох домэйн:** `is_mongolian_source()` функц

## Анхааруулга

- `deep-translator` нь Google Translate-ийн нийтийн endpoint ашигладаг. Хэт олон удаа дуудвал түр блоклож магадгүй — кэш үүний эсрэг хамгаалалт.
- Орчуулгын чанар тийм ч өндөр биш — техникийн нэр томьёо заримдаа сонин гарна. Англи эхийг доор нь үргэлж харуулдаг тул шалгах боломжтой.
- Зарим RSS feed заримдаа татагдахгүй байж болзошгүй (server алдаа, URL өөрчлөгдсөн). Тэр эх сурвалж л алгасагдана, бусад нь хэвээр ажиллана.
- `translations.json` нь `.gitignore`-д орсон тул GitHub-д push хийгдэхгүй (зөвхөн локалаар л үлдэнэ).
