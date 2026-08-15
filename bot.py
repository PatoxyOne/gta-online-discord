import os
import re
import requests
from bs4 import BeautifulSoup

URL = "https://grindmap.com/gta-online-weekly-update"
WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def get_page():
    response = requests.get(
        URL,
        timeout=30,
        headers={
            "User-Agent": "GTA-Online-Discord-Bot/1.0"
        }
    )
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def find_section(soup, keywords, limit=1000):
    for heading in soup.find_all(["h2", "h3"]):
        title = clean(
            heading.get_text(" ", strip=True)
        ).lower()

        if any(keyword.lower() in title for keyword in keywords):
            parts = []

            for element in heading.find_all_next():
                if element.name in ("h2", "h3") and element is not heading:
                    break

                text = clean(
                    element.get_text(" ", strip=True)
                )

                if text and text not in parts:
                    parts.append(text)

                if len(" ".join(parts)) >= limit:
                    break

            return clean(" ".join(parts))[:limit]

    return ""


def get_week(soup):
    text = clean(
        soup.get_text(" ", strip=True)
    )

    months = (
        r"(?:January|February|March|April|May|June|"
        r"July|August|September|October|November|December)"
    )

    match = re.search(
        rf"({months}\s+\d{{1,2}}\s+"
        rf"(?:to|-|–)\s+"
        rf"(?:{months}\s+)?\d{{1,2}},\s+\d{{4}})",
        text,
        re.I
    )

    if match:
        return match.group(1)

    return "Atualização semanal"


def find_value(text, patterns):
    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.I
        )

        if match:
            return clean(match.group(1))

    return "Veja a atualização completa."


def translate_common(text):
    translations = [
        ("Money bonuses this week", "Bônus de dinheiro desta semana"),
        ("Money bonuses", "Bônus de dinheiro"),
        ("Events and freebies", "Eventos e itens grátis"),
        ("Freebies", "Itens grátis"),
        ("Discounts worth taking", "Descontos da semana"),
        ("Discounts", "Descontos"),
        ("Podium Vehicle", "Veículo do Pódio"),
        ("Prize Ride", "Prêmio da Semana"),
        ("GTA$ & RP", "GTA$ e RP"),
        ("GTA$ and RP", "GTA$ e RP"),
        ("Rewards", "Recompensas"),
        ("Reward", "Recompensa"),
        ("Bonuses", "Bônus"),
        ("Bonus", "Bônus"),
        ("Sell Missions", "Missões de venda"),
        ("Missions", "Missões"),
        ("Mission", "Missão"),
        ("Challenges", "Desafios"),
        ("Challenge", "Desafio"),
        ("Races", "Corridas"),
        ("Race", "Corrida"),
        ("Events", "Eventos"),
        ("Free", "Grátis"),
    ]

    result = text

    for english, portuguese in translations:
        result = re.sub(
            rf"\b{re.escape(english)}\b",
            portuguese,
            result,
            flags=re.I
        )

    return clean(result)


def translate_months(text):
    months = {
        "January": "janeiro",
        "February": "fevereiro",
        "March": "março",
        "April": "abril",
        "May": "maio",
        "June": "junho",
        "July": "julho",
        "August": "agosto",
        "September": "setembro",
        "October": "outubro",
        "November": "novembro",
        "December": "dezembro"
    }

    for english, portuguese in months.items():
        text = re.sub(
            english,
            portuguese,
            text,
            flags=re.I
        )

    return text


def extract_data(soup):
    text = clean(
        soup.get_text(" ", strip=True)
    )

    podium = find_value(
        text,
        [
            r"podium vehicle.*?is\s+(?:the\s+)?"
            r"([A-Z][^.]{2,70}?)(?:\.|$)",

            r"podium.*?vehicle.*?:\s*"
            r"([A-Z][^.]{2,70}?)(?:\.|$)"
        ]
    )

    prize = find_value(
        text,
        [
            r"prize ride.*?(?:is|unlock)\s+"
            r"(?:the\s+)?([A-Z][^.]{2,70}?)(?:\.|$)",

            r"prize ride.*?:\s*"
            r"([A-Z][^.]{2,70}?)(?:\.|$)"
        ]
    )

    bonuses = find_section(
        soup,
        [
            "Money bonuses this week",
            "Money bonuses",
            "Bonuses"
        ]
    )

    events = find_section(
        soup,
        [
            "Events and freebies",
            "Events",
            "Freebies"
        ]
    )

    discounts = find_section(
        soup,
        [
            "Discounts worth taking",
            "Discounts",
            "Discount"
        ]
    )

    return {
        "podium": podium,
        "prize": prize,
        "bonuses": (
            bonuses
            or events
            or "Veja a atualização completa."
        ),
        "discounts": (
            discounts
            or "Veja a atualização completa."
        )
    }


def send_discord(week, data):

    embed = {
        "title": "🎮 GTA ONLINE — ATUALIZAÇÃO SEMANAL",

        "description": (
            f"📅 **{translate_months(week)}**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🇧🇷 Confira os principais "
            "destaques desta semana!"
        ),

        "color": 0x9146FF,

        "fields": [

            {
                "name": "💰  BÔNUS DA SEMANA",
                "value": translate_common(
                    data["bonuses"]
                )[:1024],
                "inline": False
            },

            {
                "name": "🎰  VEÍCULO DO PÓDIO",
                "value": (
                    f"**{data['podium'][:900]}**"
                ),
                "inline": False
            },

            {
                "name": "🏆  PRÊMIO DA SEMANA",
                "value": (
                    f"**{data['prize'][:900]}**"
                ),
                "inline": False
            },

            {
                "name": "🏷️  DESCONTOS",
                "value": translate_common(
                    data["discounts"]
                )[:1024],
                "inline": False
            }

        ],

        "footer": {
            "text":
                "GTA Online News 🇧🇷 • "
                "Atualizado automaticamente toda quinta-feira"
        }
    }

    payload = {
        "username": "GTA Online News 🇧🇷",

        "content":
            "🚨 **NOVA ATUALIZAÇÃO SEMANAL "
            "DO GTA ONLINE! 🇧🇷**",

        "embeds": [embed],

        "allowed_mentions": {
            "parse": []
        }
    }

    response = requests.post(
        WEBHOOK,
        json=payload,
        timeout=30
    )

    response.raise_for_status()


def main():

    if not WEBHOOK:
        raise SystemExit(
            "A Secret DISCORD_WEBHOOK_URL "
            "não foi encontrada no GitHub."
        )

    soup = get_page()

    week = get_week(soup)

    data = extract_data(soup)

    send_discord(
        week,
        data
    )

    print(
        "Atualização em português "
        "enviada para o Discord!"
    )


if __name__ == "__main__":
    main()
