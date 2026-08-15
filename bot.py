import os
import re
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import urljoin

WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")

RSS_URL = (
    "https://news.google.com/rss/search?"
    "q=site%3Arockstargames.com%2Fbr%2Fnewswire%2Farticle%20"
    "GTA%20Online"
    "&hl=pt-BR&gl=BR&ceid=BR:pt-419"
)

ROCKSTAR_DOMAIN = "https://www.rockstargames.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/130 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9"
}


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def get(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.text


def find_rockstar_url(text):
    """
    Procura diretamente URLs de artigos da Rockstar Brasil.
    """

    pattern = (
        r"https?://www\.rockstargames\.com/br/newswire/article/"
        r"[A-Za-z0-9_-]+/[^\"<>\s]+"
    )

    match = re.search(
        pattern,
        text
    )

    if match:
        return match.group(0)

    return None


def get_latest_article():

    print("Consultando notícias da Rockstar Brasil...")

    rss = get(RSS_URL)

    root = ET.fromstring(rss)

    items = root.findall(".//item")

    print(
        f"Notícias encontradas no feed: {len(items)}"
    )

    for item in items:

        title_element = item.find("title")
        link_element = item.find("link")
        description_element = item.find("description")

        title = clean(
            title_element.text
            if title_element is not None
            else ""
        )

        link = (
            link_element.text.strip()
            if link_element is not None
            and link_element.text
            else ""
        )

        description = (
            description_element.text
            if description_element is not None
            and description_element.text
            else ""
        )

        combined = (
            title
            + " "
            + link
            + " "
            + description
        )

        rockstar_url = find_rockstar_url(
            combined
        )

        if rockstar_url:

            # Remove possíveis parâmetros do Google
            rockstar_url = rockstar_url.split("?")[0]

            return {
                "title": title,
                "url": rockstar_url
            }

    return None


def get_article(url):

    print(
        "Abrindo artigo da Rockstar:"
    )

    print(url)

    html = get(url)

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # Título
    title = ""

    h1 = soup.find("h1")

    if h1:
        title = clean(
            h1.get_text(
                " ",
                strip=True
            )
        )

    if not title and soup.title:
        title = clean(
            soup.title.get_text(
                " ",
                strip=True
            )
        )

    # Data
    date = ""

    time_element = soup.find("time")

    if time_element:
        date = clean(
            time_element.get_text(
                " ",
                strip=True
            )
        )

    # Texto
    paragraphs = []

    for element in soup.find_all(
        ["p", "li"]
    ):

        text = clean(
            element.get_text(
                " ",
                strip=True
            )
        )

        if len(text) < 25:
            continue

        if text not in paragraphs:
            paragraphs.append(text)

    article_text = " ".join(
        paragraphs
    )

    return {
        "title": title,
        "date": date,
        "text": article_text,
        "url": url
    }


def create_summary(text):

    text = clean(text)

    if not text:
        return (
            "Confira todos os detalhes "
            "no artigo oficial da Rockstar Games."
        )

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    selected = []

    for sentence in sentences:

        sentence = clean(
            sentence
        )

        if len(sentence) < 35:
            continue

        selected.append(
            sentence
        )

        if len(
            " ".join(selected)
        ) >= 900:
            break

    return clean(
        " ".join(selected)
    )[:1000]


def send_discord(article):

    summary = create_summary(
        article["text"]
    )

    embed = {
        "title": (
            "🎮 GTA ONLINE — "
            "ATUALIZAÇÃO SEMANAL 🇧🇷"
        ),

        "description": (
            f"## {article['title']}\n\n"
            f"{summary}"
        ),

        "url": article["url"],

        "color": 0x9146FF,

        "fields": [
            {
                "name": "📰 FONTE OFICIAL",
                "value": (
                    "[Rockstar Games Brasil]"
                    f"({article['url']})"
                ),
                "inline": False
            }
        ],

        "footer": {
            "text": (
                "GTA Online News 🇧🇷 • "
                "Fonte: Rockstar Games"
            )
        }
    }

    payload = {
        "username": "GTA Online News 🇧🇷",

        "content": (
            "🚨 **NOVA ATUALIZAÇÃO "
            "DO GTA ONLINE! 🇧🇷**"
        ),

        "embeds": [
            embed
        ],

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

    print(
        "✅ Mensagem enviada para o Discord!"
    )


def main():

    if not WEBHOOK:
        raise SystemExit(
            "❌ A Secret "
            "DISCORD_WEBHOOK_URL "
            "não foi encontrada."
        )

    article = get_latest_article()

    if not article:
        raise SystemExit(
            "❌ Não foi possível encontrar "
            "um artigo da Rockstar Brasil."
        )

    print(
        "✅ Artigo encontrado:"
    )

    print(
        article["title"]
    )

    article_data = get_article(
        article["url"]
    )

    if not article_data["text"]:
        raise SystemExit(
            "❌ O artigo foi encontrado, "
            "mas não foi possível ler o conteúdo."
        )

    send_discord(
        article_data
    )


if __name__ == "__main__":
    main()
