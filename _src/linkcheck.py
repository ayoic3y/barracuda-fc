# -*- coding: utf-8 -*-
"""Проверка собранного сайта: внутренние ссылки + ключевые блоки.

Запуск: python _src/linkcheck.py
"""
import re
from pathlib import Path

OUT = Path("barracuda-fc")

# --- ссылки ---------------------------------------------------------------
missing = []
links_checked = 0
for page in sorted(OUT.rglob("*.html")):
    text = page.read_text(encoding="utf-8")
    for _attr, url in re.findall(r'(href|src)="([^"]+)"', text):
        if url.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:")):
            continue
        target = url.partition("#")[0]
        if not target:
            continue
        links_checked += 1
        if not (page.parent / target).resolve().exists():
            missing.append(f"{page.relative_to(OUT)} -> {url}")

# --- содержание -----------------------------------------------------------
index = (OUT / "index.html").read_text(encoding="utf-8")
matches = (OUT / "matches.html").read_text(encoding="utf-8")
squad = (OUT / "squad.html").read_text(encoding="utf-8")
club = (OUT / "club.html").read_text(encoding="utf-8")
news = (OUT / "news.html").read_text(encoding="utf-8")
all_text = " ".join(p.read_text(encoding="utf-8") for p in OUT.rglob("*.html"))

must_have = [
    "Задонатить",
    "Минский любительский (а может и каплю медиа) клуб",
    "Никогда не сдаёмся, дальше — только меньше!",
    "Следующий матч · Лига медиа команд Минска",
    "неизвестно",
    "67 школа",
    "Показываем, как делаются вещи",
    "Мы в цифрах",
    "Гонка бомбардиров",
    "Почему мы такие",
    "после 6 месяцев",
    "Приходите на 67 школу",
    "Годовщина порванных крестов Айси",
    "Радч проставил пиццу на команду",
    "100 голов в лиге",
    "Ассисты",
]
must_not_have = [
    "Приморск",
    "Купить билет",
    "Дивизион «А»",
    "Тренерский штаб",
    "Трофейная комната",
    "Веретенников",
    "Рассылка клуба",
    "Билеты и абонементы",
    "Академия",
    "VIP-ложа",
]

print("страниц:", len(list(OUT.rglob("*.html"))))
print("проверено ссылок:", links_checked, "| битых:", len(missing))
for m in missing:
    print("   !", m)

print("\nобязательные блоки:")
for phrase in must_have:
    where = []
    if phrase in index:
        where.append("главная")
    if phrase in matches:
        where.append("матчи")
    if phrase in squad:
        where.append("состав")
    if phrase in club:
        where.append("о клубе")
    if phrase in news:
        where.append("новости")
    ok = bool(where)
    print(f"   {'OK ' if ok else 'НЕТ'} {phrase[:46]:48} {', '.join(where)}")

print("\nлишнее (должно быть пусто):")
stale = [p for p in must_not_have if p in all_text]
print("   ", stale if stale else "чисто")

# --- размеры таблиц -------------------------------------------------------
def rows(html: str) -> int:
    body = html.split("<tbody>")[1].split("</tbody>")[0] if "<tbody>" in html else ""
    return body.count("<tr")

league_rows = [t for t in index.split("<tbody>")]
print("\nстрок в таблице лиги:", rows(index.split("league-table")[1]) if "league-table" in index else "?")
print("строк в таблице бомбардиров:", rows(index.split("Гонка бомбардиров")[1]) if "Гонка бомбардиров" in index else "?")
print("карточек игроков:", squad.count('class="player-card'))
print("новостных карточек на главной:", index.count('class="card news-card'))
size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file()) / 1048576
print(f"размер сайта: {size:.2f} МБ")
