# -*- coding: utf-8 -*-
"""Проверка собранного сайта: ссылки, ключевые блоки, новые правила.

Запуск: python _src/linkcheck.py
"""
import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import data as D  # noqa: E402

OUT = Path("barracuda-fc")
problems = []

# --- ссылки ---------------------------------------------------------------
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
            problems.append(f"битая ссылка: {page.relative_to(OUT)} -> {url}")

index = (OUT / "index.html").read_text(encoding="utf-8")
matches = (OUT / "matches.html").read_text(encoding="utf-8")
squad = (OUT / "squad.html").read_text(encoding="utf-8")
club = (OUT / "club.html").read_text(encoding="utf-8")
news = (OUT / "news.html").read_text(encoding="utf-8")
all_text = " ".join(p.read_text(encoding="utf-8") for p in OUT.rglob("*.html"))

print("страниц:", len(list(OUT.rglob("*.html"))))
print("проверено ссылок:", links_checked)

# --- обязательные блоки ---------------------------------------------------
must_have = [
    "Задонатить",
    "Минский любительский (а может и каплю медиа) клуб",
    "Следующий матч · Лига медиа команд Минска",
    "67 школа",
    "Показываем, как делаются вещи",
    "Как мы живём",
    "Мы в цифрах",
    "Статистика",
    "Почему мы такие",
    "ЗОЖ",
    "вылетов в турнирах",
    "после 6 месяцев",
    "Приходите поддержать",
    "промахами с метра",
    "Годовщина порванных крестов Айси",
    "Радч проставил пиццу на команду",
    "100 голов в лиге",
    "Вспомним возрождение",
    "В инстаграме обновился дизайн",
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
    "VIP-ложа",
    "Гонка бомбардиров",
    "участий в турнирах",
]

print("\nобязательные блоки:")
for phrase in must_have:
    where = [name for name, text in
             (("главная", index), ("матчи", matches), ("состав", squad),
              ("о клубе", club), ("новости", news)) if phrase in text]
    ok = bool(where)
    if not ok:
        problems.append(f"нет блока: {phrase}")
    print(f"   {'OK ' if ok else 'НЕТ'} {phrase[:44]:46} {', '.join(where)}")

print("\nлишнее (должно быть пусто):")
stale = [p for p in must_not_have if p in all_text]
print("   ", stale if stale else "чисто")
problems += [f"остался старый текст: {s}" for s in stale]

# --- новости: на главной 3, в разделе все ---------------------------------
main_cards = index.count('class="card news-card')
news_cards = news.count('class="card news-card')
print(f"\nновостей на главной: {main_cards} (должно быть 3), в разделе: {news_cards} (всего {len(D.NEWS)})")
if main_cards != 3:
    problems.append(f"на главной {main_cards} новостей вместо 3")
if news_cards != len(D.NEWS):
    problems.append(f"в разделе новостей {news_cards} карточек вместо {len(D.NEWS)}")

# --- статья: вступление не дублируется ------------------------------------
print("\nстатьи: дублей вступления быть не должно")
for item in D.NEWS:
    text = (OUT / "news" / f"{item['slug']}.html").read_text(encoding="utf-8")
    visible = text.split("<body>", 1)[-1]          # считаем только видимый текст
    excerpt_hits = visible.count(item["excerpt"])
    body_hits = visible.count(item["body"][0])
    same = item["excerpt"].strip() == item["body"][0].strip()
    ok = body_hits <= 1 and (excerpt_hits == 0 or (same and excerpt_hits == 1))
    if not ok:
        problems.append(f"дублирование в статье {item['slug']}: лид {excerpt_hits}, абзац {body_hits}")
    print(f"   {'OK ' if ok else 'ДУБЛЬ'} {item['slug'][:38]:40} лид={excerpt_hits} абзац={body_hits}")

# --- состав ---------------------------------------------------------------
nums = [int(n) for n in re.findall(r'<span class="player-num">#(\d+)</span>', squad)]
cards = squad.count('class="player-card')
ascending = nums == sorted(nums)
print(f"\nсостав: карточек {cards}, номеров {len(nums)}, по возрастанию: {ascending}")
if cards != len(D.SQUAD):
    problems.append(f"карточек состава {cards} вместо {len(D.SQUAD)}")
if not ascending:
    problems.append("карточки состава идут не по возрастанию номеров")
if " см" in squad:
    problems.append("в составе остался рост игроков")
print("   рост убран:", " см" not in squad)
print("   подписей «Год уточняется»:", squad.count("Год уточняется"))


def rows(html: str) -> int:
    body = html.split("<tbody>")[1].split("</tbody>")[0] if "<tbody>" in html else ""
    return body.count("<tr")


print("\nтаблица лиги строк:", rows(index.split("league-table")[1]) if "league-table" in index else "?")
print("таблица статистики строк:", len(D.SCORERS))

size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file()) / 1048576
print(f"размер сайта: {size:.2f} МБ")

print("\nПРОБЛЕМЫ:" if problems else "\nПроблем нет")
for p in problems:
    print("   !", p)
