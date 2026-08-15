import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")

# Página oficial da Rockstar Brasil filtrada para GTA Online
ROCKSTAR_URL = "https://www.rockstargames.com/br/newswire?tag_id=702"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/130 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def get_page(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.text


def find_articles(html):
    """
    Procura URLs de artigos da Rockstar dentro do HTML.
    """

    pattern = r'https?://www\.rockstargames\.com/br/newswire/article/[A-Za-z0-9_-]+/[^"\s<>]+'

    urls = re.findall(pattern, html)

    # Também procura URLs relativas
    relative_pattern = r'/br/newswire/article/[A-Za-z0-9_-]+/[^"\s<>]+'

    relative_urls = re.findall(
        relative_pattern,
        html
    )

    urls.extend(
        urljoin(
            "https://www.rockstargames.com",
            url
        )
        for url in relative_urls
    )

    # Remove duplicados mantendo a ordem
    result = []
    seen = set()

    for url in urls:
        url = url.replace("&amp;", "&")

        if url not in seen:
            seen.add(url)
            result.append(url)

    return result


def get_article_info(url):
    html = get_page(url)

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

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

    # Procura a data
    date = ""

    time_tag = soup.find("time")

    if time_tag:
        date = clean(
            time_tag.get_text(
                " ",
                strip=True
            )
        )

    # Texto do artigo
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

        if len(text) < 20:
            continue

        if text not in paragraphs:
            paragraphs.append(text)

    text = " ".join(paragraphs)

    return {
        "title": title,
        "date": date,
        "text": text,
        "url": url
    }


def is_gta_online(article):
    """
    Confirma que o artigo é sobre GTA Online.
    """

    title = article["title"].lower()

    gta_words = [
        "gta online",
        "grand theft auto online",
        "evento",
        "bônus",
        "bônus",
        "gta$",
        "rp",
    ]

    return any(
        word in title
        for word in gta_words
    )


def make_summary(text):
    """
    Cria um resumo simples em português,
    preservando o texto original da Rockstar.
    """

    text = clean(text)

    if not text:
        return (
            "Confira todos os detalhes "
            "na página oficial da Rockstar Games."
        )

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    result = []

    for sentence in sentences:

        sentence = clean(sentence)

        if len(sentence) < 35:
            continue

        result.append(sentence)

        if len(" ".join(result)) >= 900:
            break

    summary = clean(
        " ".join(result)
    )

    return summary[:1000]


def find_latest_article():

    print(
        "Consultando Rockstar Games Brasil..."
    )

    html = get_page(
        ROCKSTAR_URL
    )

    urls = find_articles(
        html
    )

    print(
        f"Links encontrados: {len(urls)}"
    )

    if not urls:
        return None

    articles = []

    for url in urls[:15]:

        try:

            article = get_article_info(
                url
            )

            if not article["title"]:
                continue

            if is_gta_online(
                article
            ):
                articles.append(
                    article
                )

        except Exception as error:

            print(
                "Erro ao ler artigo:",
                error
            )

    if not articles:
        return None

    return articles[0]


def send_discord(article):

    summary = make_summary(
        article["text"]
    )

    title = article["title"]

    description = (
        f"📅 **{article['date']}**\n\n"
        f"{summary}"
    )

    embed = {
        "title": (
            "🎮 GTA ONLINE — "
            "ATUALIZAÇÃO SEMANAL 🇧🇷"
        ),

        "description": description,

        "url": article["url"],

        "color": 0x9146FF,

        "fields": [
            {
                "name": "📰 Notícia oficial",
                "value": (
                    f"[Ler no Boletim da "
                    f"Rockstar Games]({article['url']})"
                ),
                "inline": False
            }
        ],

        "footer": {
            "text": (
                "GTA Online News 🇧🇷 • "
                "Fonte oficial: Rockstar Games"
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
        "Mensagem enviada para o Discord!"
    )


def main():

    if not WEBHOOK:
        raise SystemExit(
            "ERRO: a Secret "
            "DISCORD_WEBHOOK_URL "
            "não foi encontrada."
        )

    article = find_latest_article()

    if not article:
        raise SystemExit(
            "Nenhum artigo recente "
            "do GTA Online foi encontrado."
        )

    print(
        "Artigo encontrado:"
    )

    print(
        article["title"]
    )

    send_discord(
        article
    )


if __name__ == "__main__":
    main()
