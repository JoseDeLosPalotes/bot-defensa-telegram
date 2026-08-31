import os
import requests
import feedparser
from bs4 import BeautifulSoup
from google import genai

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 1. Portales de Defensa (Argentina / Región)
FEEDS_DEFENSA = [
    {"name": "Zona Militar", "url": "https://www.zona-militar.com/feed/"},
    {"name": "Defensa.com", "url": "https://www.defensa.com/rss/noticias"},
    {"name": "Pucará Defensa", "url": "https://www.pucaradefensa.com/blog-feed.xml"},
    {"name": "Noticias Militares AR", "url": "https://noticiasmilitares.ar/feed/"},
    {"name": "Gaceta Marinera", "url": "https://gacetamarinera.com.ar/feed/"}
]

# 2. Portales de Inteligencia de América Latina (Top 5)
FEEDS_INTELIGENCIA_LATAM = [
    {"name": "Insight Crime", "url": "https://es.insightcrime.org/feed/"},
    {"name": "Diálogo Américas", "url": "https://dialogo-americas.com/es/feed/"},
    {"name": "CLAME Estrategia", "url": "https://estrategia.la/feed/"},
    {"name": "Agenda Pública", "url": "https://agendapublica.elpais.com/feed"},
    {"name": "CESEM España/LATAM", "url": "http://www.cesem.org.es/feed/"}
]

# 3. Fuentes Institucionales (Argentina)
FEEDS_INSTITUCIONALES = [
    {"name": "El Parlamentario", "url": "https://www.parlamentario.com/feed/"},
    {"name": "Boletín Oficial (Sección 1era)", "url": "https://www.boletinoficial.gob.ar/rss/seccion1.xml"}
]

def extraer_noticias(lista_feeds, limite=5):
    noticias = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for item in lista_feeds:
        try:
            parsed = feedparser.parse(item["url"])
            if len(parsed.entries) > 0:
                entry = parsed.entries[0]
                noticias.append(f"[{item['name']}] Título: {entry.title} | Link: {entry.link}")
            else:
                res = requests.get(item["url"].replace("/feed/", ""), headers=headers, timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                article = soup.find('a')
                noticias.append(f"[{item['name']}] Título: {article.text.strip()} | Link: {article['href']}")
        except Exception:
            continue
            
    return "\n".join(noticias[:limite])

def obtener_alertas_bicameral_y_side():
    noticias = []
    try:
        url_busqueda = "https://news.google.com/rss/search?q=Bicameral+de+Inteligencia+OR+SIDE+OR+Inteligencia+de+Estado+Argentina&hl=es-419&gl=AR&ceid=AR:es-419"
        parsed_search = feedparser.parse(url_busqueda)
        for entry in parsed_search.entries[:4]:
            noticias.append(f"[Alerta Argentina] Título: {entry.title} | Link: {entry.link}")
    except Exception:
        pass
    return "\n".join(noticias)

def procesar_con_gemini(defensa, inteligencia_latam, institucionales, alertas_locales):
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    Actúa como un Analista Senior de Inteligencia, Seguridad Regional y Geopolítica.
    
    Recopilación de información del día:

    --- 1. NOTICIAS DE DEFENSA (ARGENTINA / REGIÓN) ---
    {defensa}

    --- 2. PORTALES DE INTELIGENCIA DE AMÉRICA LATINA ---
    {inteligencia_latam}

    --- 3. BOLETÍN OFICIAL Y PARLAMENTARIO ---
    {institucionales}

    --- 4. BICAMERAL Y INTELIGENCIA DE ESTADO (ARGENTINA) ---
    {alertas_locales}

    Genera un informe matutino estructurado exactamente así para Telegram (usando Markdown):

    🪖 *INFORME DIARIO: DEFENSA, INTELIGENCIA Y LEGISLATIVO* 🇦🇷

    1. 🛡️ *NOTICIAS TOP DE DEFENSA*
    (Resumen breve de los 5 portales con sus links)

    2. 🕵️‍♂️ *INTELIGENCIA Y SEGURIDAD LATAM*
    (Sintetiza lo más relevante de los portales de inteligencia latinoamericanos)

    3. 📜 *BOLETÍN OFICIAL Y PARLAMENTARIO*
    (Novedades normativas o legislativas clave de la jornada)

    4. 🏛️ *BICAMERAL Y INTELIGENCIA DE ESTADO (ARGENTINA)*
    (Estado de situación, novedades sobre la SIDE/DINI o el Congreso)

    5. 🎯 *CONCLUSIONES ESTRATÉGICAS*
    (2 a 3 viñetas breves con el análisis de impacto del día)

    Mantén un tono objetivo, técnico y profesional.
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    return response.text

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    defensa_raw = extraer_noticias(FEEDS_DEFENSA)
    intel_latam_raw = extraer_noticias(FEEDS_INTELIGENCIA_LATAM)
    inst_raw = extraer_noticias(FEEDS_INSTITUCIONALES, limite=3)
    alertas_raw = obtener_alertas_bicameral_y_side()
    
    informe_completo = procesar_con_gemini(defensa_raw, intel_latam_raw, inst_raw, alertas_raw)
    enviar_telegram(informe_completo)
