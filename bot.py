import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://www.rockstargames.com"
NEWSWIRE_URL = "https://www.rockstargames.com/br/newswire"
WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def get_page(url):
    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "GTA-Online-Discord-Bot/1.0"
        }
    )
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def find_latest_gta_article(soup):
    """
    Procura links recentes do GTA Online no Boletim brasileiro.
    """

    candidates = []

    for link in soup.find_all("a", href=True):

        title = clean(link.get_text(" ", strip=True))
        href = link.get("href", "")

        if not title:
            continue

        full_url = urljoin(BASE_URL, href)

        # Só queremos páginas do Newswire
        if "/br/newswire/article/" not in full_url:
            continue

        # Ignora links claramente relacionados a GTA VI
        if "gta vi" in title.lower():
            continue

        candidates.append({
            "title": title,
            "url": full_url
        })

    # Remove duplicados
    unique = []
    seen = set()

    for item in candidates:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)

    return unique[0] if unique else None


def extract_article(url):
    soup = get_page(url)

    title = ""

    # Título principal
    h1 = soup.find("h1")

    if h1:
        title = clean(h1.get_text(" ", strip=True))

    if not title and soup.title:
        title = clean(soup.title.get_text(" ", strip=True))

    # Texto do artigo
    paragraphs = []

    for element in soup.find_all(["p", "li"]):

        text = clean(
            element.get_text(" ", strip=True)
        )

        if text and text not in paragraphs:
            paragraphs.append(text)

    article_text = " ".join(paragraphs)

    return {
        "title": title or "Atualização do GTA Online",
        "text": article_text[:4000],
        "url": url
    }


def make_summary(text):
    """
    Seleciona os primeiros trechos relevantes do artigo.
    """

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    selected = []

    for sentence in sentences:

        sentence = clean(sentence)

        if len(sentence) < 30:
            continue

        selected.append(sentence)

        if len(" ".join(selected)) >= 900:
            break

    if not selected:
        return "Confira a atualização completa no Boletim da Rockstar Games."

    return clean(" ".join(selected))[:1000]


def send_discord(article):

    summary = make_summary(
        article["text"]
    )

    embed = {
        "title": "🎮 GTA ONLINE — ATUALIZAÇÃO SEMANAL 🇧🇷",

        "description": (
            f"**{article['title']}**\n\n"
            f"{summary}"
        ),

        "url": article["url"],

        "color": 0x9146FF,

        "fields": [
            {
                "name": "📰 Fonte oficial",
                "value": (
                    f"[Rockstar Games — Boletim]({article['url']})"
                ),
                "inline": False
            }
        ],

        "footer": {
            "text":
                "GTA Online News 🇧🇷 • "
                "Fonte: Rockstar Games"
        }
    }

    payload = {
        "username": "GTA Online News 🇧🇷",

        "content":
            "🚨 **NOVA ATUALIZAÇÃO DO GTA ONLINE! 🇧🇷**",

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
            "não foi encontrada."
        )

    print("Consultando Rockstar Games Brasil...")

    soup = get_page(
        NEWSWIRE_URL
    )

    article = find_latest_gta_article(
        soup
    )

    if not article:
        raise SystemExit(
            "Nenhum artigo do GTA Online foi encontrado."
        )

    print(
        "Artigo encontrado:",
        article["title"]
    )

    article_data = extract_article(
        article["url"]
    )

    send_discord(
        article_data
    )

    print(
        "Atualização enviada para o Discord!"
    )


if __name__ == "__main__":
    main()
