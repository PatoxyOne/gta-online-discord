import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://grindmap.com/gta-online-weekly-update"
STATE_FILE = Path("last_update.txt")
WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")

def clean(text):
    return re.sub(r"\\s+", " ", text).strip()

def get_page():
    r = requests.get(
        URL,
        timeout=30,
        headers={"User-Agent": "GTA-Online-Discord-Bot/1.0"},
    )
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def find_section(soup, heading_text):
    for h in soup.find_all(["h2", "h3"]):
        if heading_text.lower() in clean(h.get_text(" ", strip=True)).lower():
            parts = []
            for el in h.find_all_next():
                if el.name in ("h2", "h3") and el is not h:
                    break
                txt = clean(el.get_text(" ", strip=True))
                if txt and txt not in parts:
                    parts.append(txt)
                if len(" ".join(parts)) > 900:
                    break
            return clean(" ".join(parts))
    return ""

def get_week(soup):
    text = clean(soup.get_text(" ", strip=True))
    months = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    match = re.search(
        rf"({months}\s+\d{{1,2}}\s+(?:to|-|–)\s+(?:{months}\s+)?\d{{1,2}},\s+\d{{4}})",
        text,
        re.I,
    )
    if match:
        return match.group(1)
    return clean(soup.title.get_text()) if soup.title else "Atualização semanal"

def extract(soup):
    text = clean(soup.get_text(" ", strip=True))

    podium = re.search(
        r"podium vehicle.*?is (?:the )?([A-Z][^.]{2,70}?)(?:\.|$)",
        text,
        re.I,
    )
    prize = re.search(
        r"prize ride.*?(?:is|unlock)\s+(?:the\s+)?([A-Z][^.]{2,70}?)(?:\.|$)",
        text,
        re.I,
    )

    bonuses = find_section(soup, "Money bonuses this week")
    events = find_section(soup, "Events and freebies")
    discounts = find_section(soup, "Discounts worth taking")

    return {
        "podium": clean(podium.group(1)) if podium else "Veja a atualização completa",
        "prize": clean(prize.group(1)) if prize else "Veja a atualização completa",
        "bonuses": bonuses[:1024] or events[:1024] or "Veja a atualização completa",
        "discounts": discounts[:1024] or "Veja a atualização completa",
    }

def already_sent(week):
    return STATE_FILE.exists() and STATE_FILE.read_text(encoding="utf-8").strip() == week

def send(week, data):
    payload = {
        "username": "GTA Online News",
        "content": "🚨 **Nova atualização semanal do GTA Online!**",
        "embeds": [{
            "title": "🎮 GTA Online — Atualização Semanal",
            "description": f"📅 **{week}**\n\n[Fonte: GrindMap]({URL})",
            "color": 0x5865F2,
            "fields": [
                {"name": "🎰 Veículo do Pódio", "value": data["podium"], "inline": False},
                {"name": "🏆 Prize Ride", "value": data["prize"], "inline": False},
                {"name": "💰 Bônus / Eventos", "value": data["bonuses"], "inline": False},
                {"name": "🏷️ Descontos", "value": data["discounts"], "inline": False},
            ],
            "footer": {"text": "GTA Online News • atualização automática"},
        }],
    }

    r = requests.post(WEBHOOK, json=payload, timeout=30)
    r.raise_for_status()

def main():
    if not WEBHOOK:
        raise SystemExit("A Secret DISCORD_WEBHOOK_URL não foi configurada no GitHub.")

    soup = get_page()
    week = get_week(soup)

    if already_sent(week):
        print("Esta semana já foi enviada.")
        return

    send(week, extract(soup))
    STATE_FILE.write_text(week, encoding="utf-8")
    print("Atualização enviada ao Discord.")

if __name__ == "__main__":
    main()
