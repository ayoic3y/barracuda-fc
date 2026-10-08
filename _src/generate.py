# -*- coding: utf-8 -*-
"""Генератор статического сайта ФК «Барракуда» (Минск).

Запуск:  python _src/generate.py
Результат: папка ./barracuda-fc с готовыми HTML, CSS, JS и картинками.
Все тексты — в _src/data.py, оформление — в _src/style.css и _src/main.js.
"""
from __future__ import annotations

import html
import shutil
import sys
from datetime import datetime
from pathlib import Path

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
OUT = ROOT / "barracuda-fc"

sys.path.insert(0, str(SRC))
import data as D  # noqa: E402

CLUB = D.CLUB
NAME = CLUB["name"]
MONTHS = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]

POS_COLORS = {
    "gk": ("#22d3ee", "#1d4ed8"),
    "df": ("#60a5fa", "#1e3a8a"),
    "mf": ("#a855f7", "#5b21b6"),
    "fw": ("#c084fc", "#6d28d9"),
}
BADGE_COLORS = [
    ("#7c3aed", "#4c1d95"), ("#2563eb", "#1e3a8a"), ("#0891b2", "#0e7490"),
    ("#a855f7", "#6d28d9"), ("#3b82f6", "#1d4ed8"), ("#8b5cf6", "#3730a3"),
    ("#0ea5e9", "#075985"), ("#6366f1", "#312e81"),
]

FORM_LETTER = {"w": "W", "wp": "Wp", "d": "D", "lp": "Lp", "l": "L"}
FORM_TITLE = {
    "w": "победа", "wp": "победа по пенальти", "d": "ничья",
    "lp": "поражение по пенальти", "l": "поражение",
}
UNKNOWN_TEAM = ("неизвестно", "неизвестен", "?", "tbd")

PHOTO: dict[str, str] = {}          # номер игрока -> файл фото
NEWS_PHOTO: dict[str, str] = {}     # slug новости -> файл обложки


# ==========================================================================
# Утилиты
# ==========================================================================
def esc(value) -> str:
    return html.escape(str(value), quote=True)


def dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso)


def fmt_full(iso: str) -> str:
    d = dt(iso)
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def fmt_day(iso: str) -> str:
    d = dt(iso)
    return f"{d.day:02d}.{d.month:02d}.{d.year}"


def fmt_time(iso: str) -> str:
    return dt(iso).strftime("%H:%M")


def initials(name: str) -> str:
    """Инициалы для заглушки фото: сначала пробуем ник в скобках."""
    if "(" in name and ")" in name:
        nick = name[name.index("(") + 1:name.index(")")].strip()
        if nick:
            return nick[:2].upper()
    parts = [p for p in name.replace("«", "").replace("»", "").split() if p]
    if not parts:
        return "??"
    return parts[0][:2].upper()


def plural(n, forms) -> str:
    """forms = ("гол", "гола", "голов")."""
    n = abs(int(n)) % 100
    if 11 <= n <= 14:
        return forms[2]
    n %= 10
    if n == 1:
        return forms[0]
    if 2 <= n <= 4:
        return forms[1]
    return forms[2]


def badge_colors(name: str):
    return BADGE_COLORS[sum(ord(c) for c in name) % len(BADGE_COLORS)]


def rel(depth: int) -> str:
    return "../" * depth


def link(url: str, depth: int = 0) -> str:
    """Внутренние ссылки получают нужный префикс, внешние остаются как есть."""
    if url.startswith(("http://", "https://", "mailto:", "tel:", "#")):
        return url
    return rel(depth) + url


# ==========================================================================
# Статистика (считается из _src/data.py)
# ==========================================================================
def is_home(match) -> bool:
    return match["home"] == NAME


def our_result(match):
    if not match.get("score"):
        return None
    a, b = match["score"]
    return (a, b) if is_home(match) else (b, a)


def outcome(match):
    r = our_result(match)
    if r is None:
        return None
    return "w" if r[0] > r[1] else ("d" if r[0] == r[1] else "l")


PLAYED = [m for m in D.MATCHES if m.get("score")]
UPCOMING = [m for m in D.MATCHES if not m.get("score")]
NOW = datetime.now()
NEXT = next((m for m in UPCOMING if dt(m["date"]) >= NOW), UPCOMING[0] if UPCOMING else None)
FORM = [outcome(m) for m in PLAYED[-5:]]

CLUB_ROW = next((t for t in D.STANDINGS if t["team"] == NAME), {})
PLACE = next((i for i, t in enumerate(D.STANDINGS, start=1) if t["team"] == NAME), 0)
LEAGUE_HEAD = D.LEAGUE_HEAD
LEAGUE_NOTE = D.LEAGUE_NOTE

SCORERS = sorted(D.SCORERS, key=lambda p: -(p["goals"] + p["assists"]))

# статистика строго за последние 5 матчей (карточки на странице «Матчи»)
LAST5 = PLAYED[-5:]
L5_W = sum(1 for m in LAST5 if outcome(m) == "w")
L5_D = sum(1 for m in LAST5 if outcome(m) == "d")
L5_L = sum(1 for m in LAST5 if outcome(m) == "l")
L5_GF = sum(our_result(m)[0] for m in LAST5)
L5_GA = sum(our_result(m)[1] for m in LAST5)


# ==========================================================================
# Каркас страницы
# ==========================================================================
def head(title: str, description: str, depth: int = 0, extra_head: str = "") -> str:
    r = rel(depth)
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<script>document.documentElement.classList.add("js");</script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="theme-color" content="#08061a">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(CLUB['name_full'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:image" content="{r}assets/logo.png">
<link rel="icon" href="{r}assets/favicon.png" sizes="any">
<link rel="apple-touch-icon" href="{r}assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Oswald:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{r}css/style.css">
{extra_head}</head>
<body>"""


def header(active: str, depth: int = 0) -> str:
    r = rel(depth)
    donate = link(CLUB["donate_url"], depth)
    links = "\n".join(
        f'        <a href="{r}{href}" class="{"active" if href == active else ""}">{esc(label)}</a>'
        for href, label in D.NAV
    )
    mobile = "\n".join(
        f'      <a href="{r}{href}">{esc(label)}</a>' for href, label in D.NAV
    )
    return f"""
<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="{r}index.html">
      <span class="brand-mark"><img src="{r}assets/logo.png" alt="Эмблема ФК «{esc(NAME)}»"></span>
      <span class="brand-text">
        <span class="brand-name">{esc(NAME)}</span>
        <span class="brand-tag">{esc(CLUB['name_en'])}</span>
      </span>
    </a>
    <nav class="nav">
{links}
    </nav>
    <div class="header-actions">
      <a class="btn btn--sm" href="{donate}">Задонатить</a>
      <button class="burger" type="button" data-burger aria-label="Меню" aria-expanded="false"><span></span></button>
    </div>
  </div>
  <nav class="mobile-nav" data-mobile-nav>
{mobile}
    <a class="btn" href="{donate}">Задонатить</a>
  </nav>
</header>"""


def footer(depth: int = 0) -> str:
    r = rel(depth)
    nav_links = "\n".join(
        f'          <li><a href="{r}{href}">{esc(label)}</a></li>' for href, label in D.NAV
    )
    socials = "\n".join(
        f'          <a href="{esc(s["url"])}" title="{esc(s["title"])}" rel="noopener">{esc(s["label"])}</a>'
        for s in D.SOCIALS
    )
    return f"""
<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-col">
        <div class="footer-brand">
          <img src="{r}assets/logo.png" alt="Эмблема ФК «{esc(NAME)}»">
          <div>
            <div class="brand-name">{esc(NAME)}</div>
            <div class="brand-tag">{esc(CLUB['name_en'])}</div>
          </div>
        </div>
        <p>{esc(CLUB['slogan'])}. {esc(CLUB['motto'])}</p>
        <div class="socials">
{socials}
        </div>
      </div>
      <div class="footer-col">
        <h4>Клуб</h4>
        <ul>
{nav_links}
        </ul>
      </div>
      <div class="footer-col">
        <h4>Болельщикам</h4>
        <ul>
          <li><a href="{r}club.html#stadium">Как добраться</a></li>
          <li><a href="{r}contacts.html#faq">Вопросы и ответы</a></li>
          <li><a href="{link(CLUB['donate_url'], depth)}">Задонатить</a></li>
          <li><a href="{r}contacts.html">Связаться с клубом</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© <span data-year>2026</span> {esc(CLUB['name_full'])}. Все права защищены.</span>
      <span>г. {esc(CLUB['city'])}</span>
    </div>
  </div>
</footer>
<script src="{r}js/main.js"></script>
</body>
</html>"""


def page(filename: str, title: str, description: str, active: str, body: str,
         depth: int = 0, extra_head: str = "") -> None:
    path = OUT / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = head(title, description, depth, extra_head) + header(active, depth) + body + footer(depth)
    path.write_text(doc, encoding="utf-8", newline="\n")
    print(f"  - {filename}")


# ==========================================================================
# Компоненты
# ==========================================================================
def team_badge(team: str, depth: int = 0) -> str:
    if team == NAME:
        return (f'<span class="team-badge team-badge--light">'
                f'<img src="{rel(depth)}assets/logo.png" alt="{esc(team)}"></span>')
    if team.strip().lower() in UNKNOWN_TEAM:
        return '<span class="team-badge team-badge--unknown">?</span>'
    c1, c2 = badge_colors(team)
    return (f'<span class="team-badge" style="background:linear-gradient(140deg,{c1},{c2})">'
            f'{esc(initials(team))}</span>')


def outcome_class(match) -> str:
    return {"w": "w", "d": "d", "l": "l"}.get(outcome(match) or "", "")


def score_text(match) -> str:
    if not match.get("score"):
        return fmt_time(match["date"])
    a, b = match["score"]
    return f"{a}:{b}"


def form_dots(codes, small: bool = False) -> str:
    cls = "form-dots form-dots--sm" if small else "form-dots"
    dots = "".join(
        f'<span class="form-dot {c}" title="{esc(FORM_TITLE.get(c, c))}">{esc(FORM_LETTER.get(c, c))}</span>'
        for c in codes
    )
    return f'<span class="{cls}">{dots}</span>'


def fixture_row(match, depth: int = 0) -> str:
    tag = "Дома" if is_home(match) else "В гостях"
    cls = f'fixture-score {outcome_class(match)}' if match.get("score") else "fixture-score"
    note = f' · {esc(match["note"])}' if match.get("note") else ""
    return f"""        <div class="fixture reveal">
          <div class="fixture-date"><b>{fmt_day(match['date'])}</b>{esc(tag)}</div>
          <div>
            <div class="fixture-teams">
              <span class="home">{esc(match['home'])}</span>
              <span class="vs">—</span>
              <span class="away">{esc(match['away'])}</span>
            </div>
            <div class="fixture-venue" style="margin-top:6px">{esc(match['comp'])} · {esc(match['venue'])}{note}</div>
          </div>
          <div class="{cls}">{score_text(match)}</div>
        </div>"""


def news_card(item, depth: int = 0, wide: bool = False) -> str:
    cls = "card news-card reveal" + (" news-card--wide" if wide else "")
    photo = NEWS_PHOTO.get(item["slug"])
    if photo:
        media = (f'<div class="news-media"><img src="{rel(depth)}assets/{esc(photo)}" '
                 f'alt="{esc(item["title"])}" loading="lazy"></div>')
    else:
        media = f'<div class="news-media"><span class="glyph">{esc(item["glyph"])}</span></div>'
    return f"""        <a class="{cls}" href="{rel(depth)}news/{item['slug']}.html" data-cat="{esc(item['cat'])}">
          {media}
          <div class="news-body">
            <span class="tag">{esc(item['cat'])}</span>
            <h3>{esc(item['title'])}</h3>
            <p>{esc(item['excerpt'])}</p>
            <div class="news-meta"><span>{fmt_full(item['date'])}</span><span>{esc(item['author'])}</span></div>
          </div>
        </a>"""


def player_card(player, depth: int = 0) -> str:
    photo = PHOTO.get(str(player["num"]), f"p{player['num']}.svg")
    year = f"{player['born']} г." if player.get("born") else "Год уточняется"
    goals, assists = player["goals"], player["assists"]
    stats = (f"{goals} {plural(goals, ('гол', 'гола', 'голов'))} · "
             f"{assists} {plural(assists, ('ассист', 'ассиста', 'ассистов'))}")
    return f"""        <article class="player-card reveal" data-cat="{player['group']}">
          <div class="player-photo">
            <img src="{rel(depth)}assets/players/{photo}" alt="{esc(player['name'])}" loading="lazy">
            <span class="player-num">#{player['num']}</span>
          </div>
          <div class="player-info">
            <div class="player-name">{esc(player['name'])}</div>
            <div class="player-pos">{esc(player['pos'])}</div>
            <div class="player-meta">
              <span>{esc(year)}</span>
              <span>{stats}</span>
            </div>
          </div>
        </article>"""


def standings_table() -> str:
    rows = []
    for i, t in enumerate(D.STANDINGS, start=1):
        cls = ' class="is-club"' if t["team"] == NAME else ""
        diff = t["gf"] - t["ga"]
        diff_txt = f"+{diff}" if diff > 0 else str(diff)
        pct = round(t["pts"] / (t["played"] * 3) * 100) if t["played"] else 0
        rows.append(
            f"""          <tr{cls}>
            <td class="num">{i}</td>
            <td class="team-cell">{esc(t['team'])}</td>
            <td class="num">{t['played']}</td>
            <td class="num">{t['w']}</td>
            <td class="num">{t['wp']}</td>
            <td class="num">{t['dp']}</td>
            <td class="num">{t['l']}</td>
            <td class="num">{t['gf']}</td>
            <td class="num">{t['ga']}</td>
            <td class="num">{diff_txt}</td>
            <td class="num pts">{t['pts']}</td>
            <td class="num">{pct}%</td>
            <td>{form_dots(t['form'], small=True)}</td>
          </tr>"""
        )
    return f"""      <div class="table-wrap">
        <table class="league-table">
          <thead>
            <tr>
              <th class="num">#</th>
              <th>Команда</th>
              <th class="num" title="Матчи">И</th>
              <th class="num" title="Победы в основное время">В</th>
              <th class="num" title="Победы по пенальти">Вп</th>
              <th class="num" title="Ничьи/поражения по пенальти">Н/Пп</th>
              <th class="num" title="Поражения">П</th>
              <th class="num" title="Забитые мячи">МЗ</th>
              <th class="num" title="Пропущенные мячи">МП</th>
              <th class="num" title="Разница мячей">Р</th>
              <th class="num" title="Очки">О</th>
              <th class="num" title="Процент набранных очков">%</th>
              <th>Форма</th>
            </tr>
          </thead>
          <tbody>
{chr(10).join(rows)}
          </tbody>
        </table>
      </div>"""


def scorers_table() -> str:
    rows = []
    for i, p in enumerate(SCORERS, start=1):
        total = p["goals"] + p["assists"]
        rows.append(
            f"""          <tr>
            <td class="num">{i}</td>
            <td>{esc(p['name'])}</td>
            <td class="num">{p['goals']}</td>
            <td class="num">{p['assists']}</td>
            <td class="num pts">{total}</td>
          </tr>"""
        )
    return f"""      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th class="num">#</th><th>Игрок</th>
              <th class="num" title="Голы">Голы</th>
              <th class="num" title="Голевые передачи">Ассисты</th>
              <th class="num" title="Голы + ассисты">Всего</th>
            </tr>
          </thead>
          <tbody>
{chr(10).join(rows)}
          </tbody>
        </table>
      </div>"""


def ticker() -> str:
    items = []
    for m in PLAYED[-5:]:
        cls = {"w": "ticker-item--win", "d": "ticker-item--draw", "l": "ticker-item--loss"}[outcome(m)]
        items.append(
            f'<div class="ticker-item {cls}"><span class="dot"></span>'
            f'{esc(m["home"])} <b>{m["score"][0]}:{m["score"][1]}</b> {esc(m["away"])}</div>'
        )
    if NEXT:
        items.append(
            f'<div class="ticker-item"><span class="dot"></span>Следующий матч: '
            f'{esc(NEXT["home"])} — {esc(NEXT["away"])} · {fmt_full(NEXT["date"])} · {fmt_time(NEXT["date"])}</div>'
        )
    body = "\n        ".join(items)
    return f"""<div class="ticker">
  <div class="ticker-track" data-ticker>
        {body}
  </div>
</div>"""


def next_match_card(depth: int = 0) -> str:
    m = NEXT
    if not m:
        return ""
    return f"""      <div class="match-card reveal">
        <div class="match-card__label">Следующий матч · {esc(m['comp'])}</div>
        <div class="match-teams">
          <div class="team">
            {team_badge(m['home'], depth)}
            <span class="team-name">{esc(m['home'])}</span>
          </div>
          <span class="vs">VS</span>
          <div class="team">
            {team_badge(m['away'], depth)}
            <span class="team-name">{esc(m['away'])}</span>
          </div>
        </div>
        <div class="match-meta">
          <span>📅 {fmt_full(m['date'])}</span>
          <span>🕒 {fmt_time(m['date'])}</span>
          <span>📍 {esc(m['venue'])}</span>
        </div>
        <div class="countdown" data-countdown="{esc(m['date'])}">
          <div class="cd-item"><div class="cd-num" data-cd="d">00</div><div class="cd-label">дней</div></div>
          <div class="cd-item"><div class="cd-num" data-cd="h">00</div><div class="cd-label">часов</div></div>
          <div class="cd-item"><div class="cd-num" data-cd="m">00</div><div class="cd-label">минут</div></div>
          <div class="cd-item"><div class="cd-num" data-cd="s">00</div><div class="cd-label">секунд</div></div>
        </div>
        <div class="btn-row" style="margin-top:20px">
          <a class="btn btn--sm" href="{link(CLUB['donate_url'], depth)}">Задонатить</a>
          <a class="btn btn--sm btn--ghost" href="{rel(depth)}matches.html">Все матчи</a>
        </div>
      </div>"""


def page_hero(title: str, subtitle: str, current: str, depth: int = 0) -> str:
    return f"""
<section class="page-hero">
  <div class="container">
    <div class="breadcrumbs"><a href="{rel(depth)}index.html">Главная</a> / {esc(current)}</div>
    <h1>{esc(title)}</h1>
    <p class="lead">{esc(subtitle)}</p>
  </div>
</section>"""


def cta_band(depth: int = 0) -> str:
    return f"""
<section class="section">
  <div class="container">
    <div class="cta-band reveal">
      <h2>Приходите поддержать</h2>
      <p>А также насладиться привозами, драками, промахами с метра и незабываемыми эмоциями как в Лиге чемпионов.</p>
      <div class="btn-row mt-32">
        <a class="btn" href="{rel(depth)}club.html#stadium">Как добраться</a>
      </div>
    </div>
  </div>
</section>"""


def social_link_card(s) -> str:
    url = s["url"]
    handle = url.rstrip("/").split("/")[-1]
    if not handle.startswith("@"):
        handle = "@" + handle
    return (f'        <a class="link-card link-card--{esc(s["label"].lower())}" href="{esc(url)}"'
            f' target="_blank" rel="noopener">'
            f'<span class="link-card__label">{esc(s["title"])}</span>'
            f'<span class="link-card__value">{esc(handle)}</span>'
            f'<span class="link-card__hint">{esc(url.replace("https://", ""))}</span></a>')


def facts_cards(cards) -> str:
    return "\n".join(
        f'        <div class="card reveal" data-delay="{i * 70}"><div class="card-num">{esc(f["num"])}</div>'
        f'<div class="stat-label">{esc(f["label"])}</div></div>'
        for i, f in enumerate(cards)
    )


# ==========================================================================
# Ассеты
# ==========================================================================
def player_svg(player) -> str:
    c1, c2 = POS_COLORS[player["group"]]
    num = player["num"]
    ini = initials(player["name"])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 424" width="400" height="424" role="img" aria-label="{esc(player['name'])}">
  <defs>
    <linearGradient id="g{num}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/>
    </linearGradient>
    <radialGradient id="r{num}" cx="50%" cy="26%" r="72%">
      <stop offset="0" stop-color="#ffffff" stop-opacity=".26"/>
      <stop offset="1" stop-color="#000000" stop-opacity=".45"/>
    </radialGradient>
  </defs>
  <rect width="400" height="424" fill="#0c0824"/>
  <rect width="400" height="424" fill="url(#g{num})" opacity=".55"/>
  <rect width="400" height="424" fill="url(#r{num})"/>
  <text x="200" y="300" text-anchor="middle" font-family="Arial Black, Arial, sans-serif" font-size="230" font-weight="900" fill="#ffffff" opacity=".14">{num}</text>
  <g fill="#ffffff" opacity=".22">
    <circle cx="200" cy="128" r="46"/>
    <path d="M92 356c6-92 50-146 108-146s102 54 108 146z"/>
  </g>
  <text x="200" y="392" text-anchor="middle" font-family="Arial Black, Arial, sans-serif" font-size="30" font-weight="900" fill="#ffffff" opacity=".62" letter-spacing="4">{ini}</text>
</svg>
"""


def write_assets() -> None:
    assets = OUT / "assets"
    players = assets / "players"
    players.mkdir(parents=True, exist_ok=True)

    static = ["logo.png", "logo.svg", "favicon.png", "favicon-32.png", "favicon.svg",
              "apple-touch-icon.png", "map-67.jpg"]
    for name in static:
        src = SRC / "assets" / name
        if src.exists():
            shutil.copy2(src, assets / name)

    # Фото игроков: _src/assets/players/p<номер>.jpg|png — заменяет заглушку
    photo_dir = SRC / "assets" / "players"
    for p in D.SQUAD:
        real = None
        if photo_dir.exists():
            for ext in ("jpg", "jpeg", "png", "webp"):
                candidate = photo_dir / f"p{p['num']}.{ext}"
                if candidate.exists():
                    real = candidate
                    break
        if real:
            shutil.copy2(real, players / real.name)
            PHOTO[str(p["num"])] = real.name
        else:
            (players / f"p{p['num']}.svg").write_text(player_svg(p), encoding="utf-8")

    # Обложки новостей: файл из _src/assets/news/, путь указывается в data.py ("image")
    for item in D.NEWS:
        image = (item.get("image") or "").strip()
        if not image:
            continue
        src = SRC / "assets" / image
        if src.exists():
            dst = assets / image
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            NEWS_PHOTO[item["slug"]] = image
        else:
            print(f"    ! обложка не найдена: _src/assets/{image}")

    (OUT / "css").mkdir(parents=True, exist_ok=True)
    (OUT / "js").mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC / "style.css", OUT / "css" / "style.css")
    shutil.copy2(SRC / "main.js", OUT / "js" / "main.js")


# ==========================================================================
# Главная
# ==========================================================================
def build_index() -> None:
    latest = D.NEWS[:3]
    news_html = "\n".join(news_card(n, 0, wide=(i == 0)) for i, n in enumerate(latest))
    results_html = "\n".join(fixture_row(m) for m in PLAYED[-5:][::-1])
    values = "\n".join(
        f'        <div class="card reveal" data-delay="{i * 80}"><h3>{esc(v["title"])}</h3><p>{esc(v["text"])}</p></div>'
        for i, v in enumerate(D.CLUB_VALUES)
    )
    st = CLUB["stadium"]

    json_ld = """<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SportsTeam",
  "name": "ФК Барракуда",
  "alternateName": "Barracuda FC",
  "sport": "Футбол",
  "foundingDate": "2023",
  "logo": "assets/logo.png",
  "location": { "@type": "Place", "name": "67 школа", "address": "г. Минск, улица И.Я. Алибегова, 5А" }
}
</script>
"""

    body = f"""
<section class="hero">
  <div class="container hero-grid">
    <div>
      <img class="hero-crest reveal" src="assets/logo.png" alt="Эмблема ФК «{esc(NAME)}»">
      <div class="eyebrow">Сезон {esc(CLUB['season'])} · {esc(CLUB['league'])}</div>
      <h1>Футбольный клуб<span>«{esc(NAME)}»</span></h1>
      <p class="lead">{esc(CLUB['slogan'])}. {esc(CLUB['motto'])}</p>
      <div class="btn-row mt-32">
        <a class="btn" href="{link(CLUB['donate_url'])}">Задонатить</a>
        <a class="btn btn--ghost" href="squad.html">Состав команды</a>
      </div>
      <div class="hero-stats">
        <div><div class="stat-num">{CLUB_ROW.get('pts', 0)}</div><div class="stat-label">Очки в лиге</div></div>
        <div><div class="stat-num">{PLACE}</div><div class="stat-label">Место в таблице</div></div>
        <div><div class="stat-num">{CLUB_ROW.get('gf', 0)}</div><div class="stat-label">Забитых мячей</div></div>
        <div><div class="stat-num">{CLUB_ROW.get('played', 0)}</div><div class="stat-label">Матчей в лиге</div></div>
      </div>
    </div>
{next_match_card(0)}
  </div>
</section>

{ticker()}

<section class="section">
  <div class="container">
    <div class="section-head">
      <div>
        <div class="eyebrow">Последние матчи</div>
        <h2>Показываем, как делаются вещи</h2>
        <p>Форма в последних 5 встречах: {form_dots(FORM)}</p>
      </div>
      <a class="btn btn--ghost btn--sm" href="matches.html">Календарь и таблица</a>
    </div>
    <div class="fixtures">
{results_html}
    </div>
  </div>
</section>

<section class="section section--soft">
  <div class="container">
    <div class="section-head">
      <div>
        <div class="eyebrow">Новости клуба</div>
        <h2>Как мы живём</h2>
      </div>
      <a class="btn btn--ghost btn--sm" href="news.html">Все новости</a>
    </div>
    <div class="grid grid-3">
{news_html}
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head">
      <div>
        <div class="eyebrow">Статистика</div>
        <h2>Мы в цифрах</h2>
        <p>{esc(CLUB['intro'])}</p>
      </div>
      <a class="btn btn--ghost btn--sm" href="club.html">О клубе</a>
    </div>
    <div class="grid grid-4">
{facts_cards(D.CLUB_FACTS)}
    </div>
  </div>
</section>

<section class="section section--soft">
  <div class="container">
    <div class="grid grid-2" style="align-items:start;gap:34px">
      <div>
        <div class="eyebrow">Лидеры</div>
        <h2>Статистика</h2>
        <p>Лучшие снайперы, которые целятся по воробьям, а попадают по воротам</p>
{scorers_table()}
      </div>
      <div>
        <div class="eyebrow">Ценности</div>
        <h2>Почему мы такие</h2>
        <div class="grid" style="gap:14px">
{values}
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head">
      <div>
        <div class="eyebrow">Таблица</div>
        <h2>{esc(LEAGUE_HEAD)}</h2>
        <p>{esc(LEAGUE_NOTE)}</p>
      </div>
      <a class="btn btn--ghost btn--sm" href="matches.html#table">Вся таблица</a>
    </div>
{standings_table()}
  </div>
</section>

{cta_band(0)}
"""
    page("index.html", f"ФК «{NAME}» — официальный сайт команды",
         f"Официальный сайт ФК «{NAME}»: состав, календарь и результаты матчей, таблица {CLUB['league']}, новости и статистика.",
         "index.html", body, 0, extra_head=json_ld)


# ==========================================================================
# Матчи
# ==========================================================================
def build_matches() -> None:
    upcoming = "\n".join(fixture_row(m) for m in UPCOMING)
    played = "\n".join(fixture_row(m) for m in reversed(PLAYED))
    st = CLUB["stadium"]
    body = page_hero("Матчи",
                     f"Календарь и результаты сезона {CLUB['season']} в {CLUB['league']}, турнирная таблица и форма команды.",
                     "Матчи") + f"""
<section class="section">
  <div class="container">
    <div class="section-head">
      <div>
        <div class="eyebrow">Форма команды</div>
        <h2>Последние пять матчей</h2>
      </div>
      <div>{form_dots(FORM)}</div>
    </div>
    <div class="grid grid-4">
      <div class="card reveal"><div class="card-num">{L5_W}</div><div class="stat-label">Побед за последние 5 матчей</div></div>
      <div class="card reveal" data-delay="80"><div class="card-num">{L5_D}</div><div class="stat-label">Ничьих</div></div>
      <div class="card reveal" data-delay="160"><div class="card-num">{L5_L}</div><div class="stat-label">Поражений</div></div>
      <div class="card reveal" data-delay="240"><div class="card-num">{L5_GF}:{L5_GA}</div><div class="stat-label">Забитые и пропущенные</div></div>
    </div>
  </div>
</section>

<section class="section section--soft" id="calendar">
  <div class="container">
    <div data-tabs>
      <div class="tabs">
        <button class="tab active" type="button" data-tab="cal" aria-selected="true">Календарь</button>
        <button class="tab" type="button" data-tab="res" aria-selected="false">Результаты</button>
        <button class="tab" type="button" data-tab="tbl" aria-selected="false">Таблица</button>
      </div>

      <div class="tabpanel active" data-panel="cal">
        <h2>Ближайшие матчи</h2>
        <p class="lead">Домашние игры — {esc(st['name'])}, {esc(st['address'])}.</p>
        <div class="fixtures" style="margin-top:24px">
{upcoming}
        </div>
      </div>

      <div class="tabpanel" data-panel="res">
        <h2>Результаты сезона {esc(CLUB['season'])}</h2>
        <p class="lead">Все сыгранные матчи — от игры с «Уан Медиа» до победы над «Снейкс».</p>
        <div class="fixtures" style="margin-top:24px">
{played}
        </div>
      </div>

      <div class="tabpanel" data-panel="tbl" id="table">
        <h2>{esc(LEAGUE_HEAD)}</h2>
        <p class="lead">{esc(LEAGUE_NOTE)}</p>
        <div style="margin-top:24px">
{standings_table()}
        </div>
      </div>
    </div>
  </div>
</section>

{cta_band(0)}
"""
    page("matches.html", f"Матчи — ФК «{NAME}»",
         f"Календарь и результаты ФК «{NAME}»: таблица {CLUB['league']}, форма команды и все сыгранные матчи.",
         "matches.html", body)


# ==========================================================================
# Состав
# ==========================================================================
def build_squad() -> None:
    # карточки идут в порядке возрастания номеров
    squad = sorted(D.SQUAD, key=lambda p: p["num"])
    cards = "\n".join(player_card(p) for p in squad)
    if D.STAFF:
        staff_cards = "\n".join(
            f"""        <div class="card staff-card reveal" data-delay="{i * 70}">
          <div class="staff-avatar">{esc(initials(s['name']))}</div>
          <div class="player-name">{esc(s['name'])}</div>
          <div class="staff-role">{esc(s['role'])}</div>
          <p style="margin-top:12px;font-size:.9rem">{esc(s['note'])}</p>
        </div>"""
            for i, s in enumerate(D.STAFF)
        )
    else:
        staff_cards = (f'        <div class="card reveal" style="grid-column:1/-1">'
                       f'<p style="margin:0;font-size:.95rem">{esc(D.STAFF_EMPTY_TEXT)}</p></div>')
    chips = []
    for key, label in D.SQUAD_GROUPS:
        active = " active" if key == "all" else ""
        chips.append(
            f'        <button class="chip{active}" type="button" data-filter="{esc(key)}">{esc(label)}</button>'
        )
    chips.append(
        f'        <span class="muted" style="align-self:center;margin-left:6px">игроков: '
        f'<b data-filter-count>{len(D.SQUAD)}</b></span>'
    )
    chips_html = "\n".join(chips)
    ages = [NOW.year - p["born"] for p in D.SQUAD if p.get("born")]
    avg_age = round(sum(ages) / len(ages)) if ages else 0
    body = page_hero("Состав",
                     f"{len(D.SQUAD)} {plural(len(D.SQUAD), ('игрок', 'игрока', 'игроков'))} в заявке, средний возраст {avg_age} лет.",
                     "Состав") + f"""
<section class="section">
  <div class="container">
    <div class="grid grid-4" style="margin-bottom:34px">
      <div class="card reveal"><div class="card-num">{len(D.SQUAD)}</div><div class="stat-label">Игрока в заявке</div></div>
      <div class="card reveal" data-delay="80"><div class="card-num">{CLUB_ROW.get('gf', 0)}</div><div class="stat-label">Забитых мячей в лиге</div></div>
      <div class="card reveal" data-delay="160"><div class="card-num">{CLUB_ROW.get('pts', 0)}</div><div class="stat-label">Очки в лиге</div></div>
      <div class="card reveal" data-delay="240"><div class="card-num">{PLACE}</div><div class="stat-label">Место в таблице</div></div>
    </div>

    <div class="section-head">
      <div>
        <div class="eyebrow">Заявка на сезон {esc(CLUB['season'])}</div>
        <h2>Игроки</h2>
        <p>Вратари, защитники, полузащитники и нападающие.</p>
      </div>
    </div>

    <div class="filters" data-filter-group data-filter-scope="#squadGrid" style="margin-bottom:26px">
{chips_html}
    </div>

    <div class="squad-grid" id="squadGrid">
{cards}
    </div>
  </div>
</section>

<section class="section section--soft">
  <div class="container">
    <div class="section-head">
      <div>
        <div class="eyebrow">Штаб</div>
        <h2>Тренерский штаб</h2>
        <p>Тренеры, аналитик и врач команды.</p>
      </div>
    </div>
    <div class="grid grid-2">
{staff_cards}
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head">
      <div>
        <div class="eyebrow">Лидеры</div>
        <h2>Статистика</h2>
        <p>Лучшие снайперы, которые целятся по воробьям, а попадают по воротам</p>
      </div>
    </div>
{scorers_table()}
  </div>
</section>
"""
    page("squad.html", f"Состав — ФК «{NAME}»",
         f"Состав ФК «{NAME}»: игроки команды, голы и голевые передачи.",
         "squad.html", body)


# ==========================================================================
# Новости
# ==========================================================================
def build_news() -> None:
    featured = D.NEWS[0]
    rest = D.NEWS[1:]
    cards = "\n".join(news_card(n) for n in rest)
    chips = []
    for i, cat in enumerate(D.NEWS_CATS):
        value = "all" if i == 0 else cat
        active = " active" if i == 0 else ""
        chips.append(
            f'        <button class="chip{active}" type="button" data-filter="{esc(value)}">{esc(cat)}</button>'
        )
    chips.append(
        f'        <span class="muted" style="align-self:center;margin-left:6px">материалов: '
        f'<b data-filter-count>{len(D.NEWS)}</b></span>'
    )
    chips_html = "\n".join(chips)
    body = page_hero("Новости клуба",
                     "Всё, что происходит в «Барракуде»: матчи, люди, истории.",
                     "Новости") + f"""
<section class="section">
  <div class="container">
    <div class="filters" data-filter-group data-filter-scope="#newsGrid" style="margin-bottom:26px">
{chips_html}
    </div>

    <div class="grid grid-3" id="newsGrid">
{news_card(featured, 0, wide=True)}
{cards}
    </div>
  </div>
</section>

{cta_band(0)}
"""
    page("news.html", f"Новости — ФК «{NAME}»",
         f"Новости ФК «{NAME}»: матчи, люди и истории команды.",
         "news.html", body)

    for item in D.NEWS:
        paragraphs = "\n".join(f"      <p>{esc(p)}</p>" for p in item["body"])
        photo = NEWS_PHOTO.get(item["slug"])
        image_html = (f'    <img class="article-img" src="../assets/{esc(photo)}" '
                      f'alt="{esc(item["title"])}">') if photo else ""
        others = [n for n in D.NEWS if n["slug"] != item["slug"]][:3]
        related = "\n".join(news_card(n, 1) for n in others)
        article_body = f"""
<article>
<section class="page-hero">
  <div class="container">
    <div class="breadcrumbs"><a href="../index.html">Главная</a> / <a href="../news.html">Новости</a> / {esc(item['cat'])}</div>
    <span class="tag">{esc(item['cat'])}</span>
    <h1 style="margin-top:16px">{esc(item['title'])}</h1>
    <p class="muted">{fmt_full(item['date'])} · {esc(item['author'])}</p>
  </div>
</section>

<section class="section">
  <div class="container" style="max-width:820px">
{image_html}
{paragraphs}
    <div class="btn-row mt-32">
      <a class="btn btn--ghost btn--sm" href="../news.html">← Все новости</a>
      <a class="btn btn--sm" href="{link(CLUB['donate_url'], 1)}">Задонатить</a>
    </div>
  </div>
</section>
</article>

<section class="section section--soft">
  <div class="container">
    <div class="section-head"><div><div class="eyebrow">Читайте также</div><h2>Другие материалы</h2></div></div>
    <div class="grid grid-3">
{related}
    </div>
  </div>
</section>
"""
        page(f"news/{item['slug']}.html", f"{item['title']} — ФК «{NAME}»",
             item["excerpt"], "news.html", article_body, 1)


# ==========================================================================
# О клубе
# ==========================================================================
def build_club() -> None:
    timeline = "\n".join(
        f"""        <div class="tl-item reveal">
          <div class="tl-year">{esc(year)}</div>
          <p>{esc(text)}</p>
        </div>"""
        for year, text in D.TIMELINE
    )
    st = CLUB["stadium"]
    body = page_hero(f"О клубе «{NAME}»",
                     f"{CLUB['slogan']}. {CLUB['motto']}",
                     "О клубе") + f"""
<section class="section">
  <div class="container">
    <div class="section-head">
      <div>
        <div class="eyebrow">Статистика</div>
        <h2>Мы в цифрах</h2>
        <p>{esc(CLUB['intro'])}</p>
      </div>
    </div>
    <div class="grid grid-4">
{facts_cards(D.CLUB_FACTS)}
    </div>
  </div>
</section>

<section class="section section--soft">
  <div class="container">
    <div class="grid grid-2" style="gap:34px;align-items:start">
      <div>
        <div class="eyebrow">Наша история</div>
        <h2>Как всё начиналось</h2>
        <p>{esc(CLUB['history'])}</p>
        <p>Команда играет в {esc(CLUB['league'])}. После 6 месяцев сезона {esc(CLUB['season'])} «Барракуда» идёт третьей в таблице: {CLUB_ROW.get('w', 0)} побед в основное время, {CLUB_ROW.get('wp', 0)} по пенальти, {CLUB_ROW.get('gf', 0)} забитых мячей.</p>
        <p>{esc(CLUB['motto'])}</p>
      </div>
      <div class="timeline">
{timeline}
      </div>
    </div>
  </div>
</section>

<section class="section" id="stadium">
  <div class="container">
    <div class="grid grid-2" style="gap:34px;align-items:center">
      <div>
        <div class="eyebrow">Домашняя площадка</div>
        <h2>{esc(st['name'])}</h2>
        <p>Домашние матчи «Барракуда» играет в {esc(st['name'].lower())}: {esc(st['surface'])}, вместимость — {st['capacity']} человек. Приходите болеть: вход свободный.</p>
        <div class="info-list mt-32">
          <div class="info-row"><span class="ico">📍</span><div><b>Адрес</b><span>г. {esc(CLUB['city'])}, {esc(st['address'])}</span></div></div>
          <div class="info-row"><span class="ico">🕒</span><div><b>Начало матчей</b><span>даты и время — в разделе «Матчи»</span></div></div>
          <div class="info-row"><span class="ico">🚌</span><div><b>Как добраться</b><span>метро «Малиновка», далее автобусами до остановки «Алибегова»</span></div></div>
          <div class="info-row"><span class="ico">🎟️</span><div><b>Вход</b><span>свободный — приходите с друзьями и в цветах клуба</span></div></div>
        </div>
      </div>
      <div class="map-photo" style="--pin-x:{esc(CLUB['map']['pin_x'])};--pin-y:{esc(CLUB['map']['pin_y'])}">
        <img src="assets/{esc(CLUB['map']['image'])}" alt="Карта: {esc(st['name'])}, {esc(CLUB['city'])}" loading="lazy">
        <span class="pin pin--on-map" title="{esc(st['name'])}"></span>
        <div class="map-photo__caption">
          <div class="player-name">{esc(st['name'])}</div>
          <p class="muted" style="margin:4px 0 0">г. {esc(CLUB['city'])}, {esc(st['address'])}</p>
        </div>
      </div>
    </div>
  </div>
</section>

{cta_band(0)}
"""
    page("club.html", f"О клубе — ФК «{NAME}»",
         f"История, цифры и домашняя площадка ФК «{NAME}» из Минска.",
         "club.html", body)


# ==========================================================================
# Контакты
# ==========================================================================
def build_contacts() -> None:
    faq = "\n".join(
        f"""        <details class="faq-item reveal">
          <summary>{esc(q)}</summary>
          <p>{esc(a)}</p>
        </details>"""
        for q, a in D.FAQ
    )
    topics = "\n".join(f"              <option>{esc(t)}</option>" for t in D.CONTACT_TOPICS)
    links = "\n".join(social_link_card(s) for s in D.SOCIALS)
    body = page_hero("Контакты",
                     "Как связаться с клубом и где нас найти в соцсетях.",
                     "Контакты") + f"""
<section class="section">
  <div class="container">
    <div class="grid grid-2" style="gap:34px;align-items:start">
      <div>
        <div class="eyebrow">Написать клубу</div>
        <h2>Форма обратной связи</h2>
        <p>Хотите в состав, есть вопрос по матчу, идея для контента или предложение о партнёрстве — пишите.</p>
        <form class="form mt-32" action="thanks.html" method="get">
          <div class="field">
            <label for="name">Имя</label>
            <input id="name" name="name" type="text" placeholder="Как к вам обращаться" required>
          </div>
          <div class="field">
            <label for="contact">Связь</label>
            <input id="contact" name="contact" type="text" placeholder="Telegram, телефон или e-mail" required>
          </div>
          <div class="field">
            <label for="topic">Тема</label>
            <select id="topic" name="topic">
{topics}
            </select>
          </div>
          <div class="field">
            <label for="message">Сообщение</label>
            <textarea id="message" name="message" placeholder="Расскажите, чем можем помочь"></textarea>
          </div>
          <button class="btn" type="submit">Отправить</button>
          <span class="form-note" data-form-note>Нажимая кнопку, вы соглашаетесь на обработку персональных данных.</span>
        </form>
      </div>

      <div>
        <div class="eyebrow">Мы в сети</div>
        <h2>Соцсети команды</h2>
        <p>Все анонсы, составы и разборы матчей — здесь. Заходите и подписывайтесь.</p>
        <div class="link-cards mt-32">
{links}
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section section--soft" id="faq">
  <div class="container" style="max-width:900px">
    <div class="section-head">
      <div>
        <div class="eyebrow">FAQ</div>
        <h2>Частые вопросы</h2>
        <p>Не нашли ответ? Напишите в форме выше.</p>
      </div>
    </div>
{faq}
  </div>
</section>
"""
    page("contacts.html", f"Контакты — ФК «{NAME}»",
         f"Как связаться с ФК «{NAME}», где проходят матчи и как поддержать клуб.",
         "contacts.html", body)


# ==========================================================================
# Служебные страницы и файлы
def build_thanks() -> None:
    body = f"""
<section class="section">
  <div class="container center" style="padding:70px 0;max-width:820px">
    <p style="font-size:1.45rem;font-weight:700;line-height:1.45;margin:0 0 32px">
      <strong>{esc(D.CONTACT_THANKS)}</strong>
    </p>
    <div class="btn-row" style="justify-content:center">
      <a class="btn" href="index.html">На главную</a>
      <a class="btn btn--ghost" href="news.html">Новости клуба</a>
    </div>
  </div>
</section>
"""
    page("thanks.html", f"Спасибо — ФК «{NAME}»",
         "Спасибо за ваше сообщение!", "", body)


def build_donate() -> None:
    d = D.DONATE
    body = page_hero(d["title"], d["note"], d["title"]) + f"""
<section class="section">
  <div class="container center" style="max-width:780px">
    <p style="margin:0 0 10px;font-size:.76rem;letter-spacing:.2em;text-transform:uppercase;color:var(--muted)">Карта для перевода</p>
    <p style="font-family:var(--font-head);font-size:clamp(1.25rem,3.6vw,2rem);font-weight:700;letter-spacing:.04em;margin:0 0 12px">
      <strong>{esc(d['card'])}</strong>
    </p>
    <p style="font-size:1.15rem;font-weight:700;margin:0 0 30px"><strong>{esc(d['bank'])}</strong></p>
    <p class="muted" style="margin-bottom:30px">Переведите любую сумму — этого достаточно. Спасибо, что поддерживаете команду.</p>
    <div class="btn-row" style="justify-content:center">
      <a class="btn" href="index.html">На главную</a>
      <a class="btn btn--ghost" href="contacts.html">Связаться с клубом</a>
    </div>
  </div>
</section>
"""
    page("donate.html", f"Задонатить — ФК «{NAME}»",
         "Реквизиты карты для поддержки команды.", "", body)


# ==========================================================================
def build_service() -> None:
    page("404.html", f"Страница не найдена — ФК «{NAME}»",
         "Такой страницы на сайте клуба нет.",
         "", """
<section class="section">
  <div class="container center" style="padding:60px 0">
    <div class="eyebrow">Ошибка 404</div>
    <h1>Мяч ушёл за пределы поля</h1>
    <p class="lead" style="margin:0 auto 28px">Такой страницы нет. Вернитесь на главную или посмотрите ближайшие матчи команды.</p>
    <div class="btn-row" style="justify-content:center">
      <a class="btn" href="index.html">На главную</a>
      <a class="btn btn--ghost" href="matches.html">Матчи</a>
    </div>
  </div>
</section>
""")

    urls = ["index.html", "matches.html", "squad.html", "news.html", "club.html",
            "contacts.html", "donate.html"]
    urls += [f"news/{n['slug']}.html" for n in D.NEWS]
    today = datetime.now().strftime("%Y-%m-%d")
    site = CLUB.get("site_url", "").rstrip("/")
    entries = "\n".join(
        f"  <url><loc>{site}/{u}</loc><lastmod>{today}</lastmod></url>" for u in urls
    )
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {site}/sitemap.xml\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print("  - sitemap.xml, robots.txt, .nojekyll")


# ==========================================================================
def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    print(f"Сборка сайта ФК «{NAME}»")
    write_assets()
    print("  - css/style.css, js/main.js, assets/")
    build_index()
    build_matches()
    build_squad()
    build_news()
    build_club()
    build_contacts()
    build_thanks()
    build_donate()
    build_service()
    total = len(list(OUT.rglob("*.html")))
    print(f"Готово: {total} HTML-страниц")


if __name__ == "__main__":
    main()
