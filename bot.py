import os
import re
import requests
from bs4 import BeautifulSoup

URL = "https://grindmap.com/gta-online-weekly-update"
WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")

def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()

def get_page():
    r = requests.get(
        URL,
        timeout=30,
        headers={"User-Agent": "GTA-Online-Discord-Bot/1.0"},
    )
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def find_section(soup, keywords, limit=900):
    for h in soup.find_all(["h2", "h3"]):
        heading = clean(h.get_text(" ", strip=True)).lower()
        if any(k.lower() in heading for k in keywords):
            parts = []
            for el in h.find_all_next():
                if el.name in ("h2", "h3") and el is not h:
                    break
                txt = clean(el.get_text(" ", strip=True))
                if txt and txt not in parts:
                    parts.append(txt)
                if len(" ".join(parts)) >= limit:
                    break
            return clean(" ".join(parts))[:limit]
    return ""

def get_week(soup):
    text = clean(soup.get_text(" ", strip=True))
    months = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    m = re.search(
        rf"({months}\s+\d{{1,2}}\s+(?:to|-|–)\s+(?:{months}\s+)?\d{{1,2}},\s+\d{{4}})",
        text,
        re.I,
    )
    return m.group(1) if m else "Atualização semanal"

def find_value(text, patterns):
    for pattern in patterns:
        m = re.search(pattern, text, re.I)
        if m:
            return clean(m.group(1))
    return "Veja a atualização completa"

def extract_data(soup):
    text = clean(soup.get_text(" ", strip=True))

    podium = find_value(text, [
        r"podium vehicle.*?is\s+(?:the\s+)?([A-Z][^.]{2,70}?)(?:\.|$)",
        r"podium.*?vehicle.*?:\s*([A-Z][^.]{2,70}?)(?:\.|$)",
    ])

    prize = find_value(text, [
        r"prize ride.*?(?:is|unlock)\s+(?:the\s+)?([A-Z][^.]{2,70}?)(?:\.|$)",
        r"prize ride.*?:\s*([A-Z][^.]{2,70}?)(?:\.|$)",
    ])

    bonuses = find_section(
        soup,
        ["Money bonuses this week", "Money bonuses", "Bonuses"],
        1000,
    )

    events = find_section(
        soup,
        ["Events and freebies", "Events", "Freebies"],
        1000,
    )

    discounts = find_section(
        soup,
        ["Discounts worth taking", "Discounts", "Discount"],
        1000,
    )

    return {
        "podium": podium,
        "prize": prize,
        "bonuses": bonuses or events or "Veja a atualização completa.",
        "discounts": discounts or "Veja a atualização completa.",
    }

def send_discord(week, data):
    embed = {
        "title": "🎮 GTA ONLINE — EVENT WEEK",
        "description": (
            f"📅 **{week}**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Confira abaixo os principais destaques da semana."
        ),
        "color": 0x9146FF,
        "fields": [
            {
                "name": "💰  BÔNUS DA SEMANA",
                "value": data["bonuses"][:1024],
                "inline": False,
            },
            {
                "name": "🎰  VEÍCULO DO PÓDIO",
                "value": f"**{data['podium'][:900]}**",
                "inline": False,
            },
            {
                "name": "🏆  PRIZE RIDE",
                "value": f"**{data['prize'][:900]}**",
                "inline": False,
            },
            {
                "name": "🏷️  DESCONTOS",
                "value": data["discounts"][:1024],
                "inline": False,
            },
        ],
        "thumbnail": {
            "url": "https://www.rockstargames.com/rockstargames.png"
        },
        "footer": {
            "text": "GTA Online News • atualização automática toda quinta-feira"
        },
    }

    payload = {
        "username": "GTA Online News",
        "content": "🚨 **NOVA ATUALIZAÇÃO SEMANAL DO GTA ONLINE!**",
        "embeds": [embed],
        "allowed_mentions": {"parse": []},
    }

    response = requests.post(WEBHOOK, json=payload, timeout=30)
    response.raise_for_status()

def main():
    if not WEBHOOK:
        raise SystemExit(
            "A Secret DISCORD_WEBHOOK_URL não foi encontrada no GitHub."
        )

    soup = get_page()
    week = get_week(soup)
    data = extract_data(soup)

    send_discord(week, data)
    print("Atualização enviada para o Discord!")

if __name__ == "__main__":
    main()
