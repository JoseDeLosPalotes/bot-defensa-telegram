import os
import requests
import feedparser
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

FEEDS = [
    {"name": "Zona Militar", "url": "https://www.zona-militar.com/feed/"},
    {"name": "Defensa.com", "url": "https://www.defensa.com/rss/noticias"},
    {"name": "Pucará Defensa", "url": "https://www.pucaradefensa.com/blog-feed.xml"},
    {"name": "Noticias Militares AR", "url": "https://noticiasmilitares.ar/feed/"},
    {"name": "Gaceta Marinera", "url": "https://gacetamarinera.com.ar/feed/"}
]

def obtener_noticias():
    noticias = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for item in FEEDS:
        try:
            parsed = feedparser.parse(item["url"])
            if len(parsed.entries) > 0:
                entry = parsed.entries[0]
                noticias.append(f"🔹 *{item['name']}*\n[{entry.title}]({entry.link})")
            else:
                res = requests.get(item["url"].replace("/feed/", ""), headers=headers, timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                article = soup.find('a')
                noticias.append(f"🔹 *{item['name']}*\n[{article.text.strip()}]({article['href']})")
        except Exception:
            noticias.append(f"🔹 *{item['name']}*\n[Visitar portal]({item['url'].replace('/feed/', '')})")
            
    return noticias[:5]

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    lista = obtener_noticias()
    encabezado = "🪖 *RESUMEN DIARIO DE DEFENSA* 🇦🇷\n\nPrincipales portales de la región:\n\n"
    cuerpo = "\n\n".join(lista)
    
    enviar_telegram(encabezado + cuerpo)
