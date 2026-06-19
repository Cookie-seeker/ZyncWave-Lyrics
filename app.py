import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

#Configuración
BASE_URL   = "https://music.youtube.com/youtubei/v1"
API_KEY    = "AIzaSyC9XL3ZjWdtnsGnGoMT-OQXHK0WKVQHQ"
TIMEOUT    = 15

# Cookies y auth desde variables de entorno
YT_COOKIE  = os.environ.get("YT_COOKIE", "")
YT_AUTH    = os.environ.get("YT_AUTH", "")
YT_VISITOR = os.environ.get("YT_VISITOR_ID", "")

def get_headers():
    return {
        "Content-Type":             "application/json",
        "User-Agent":               "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Origin":                   "https://music.youtube.com",
        "Referer":                  "https://music.youtube.com/",
        "X-Youtube-Client-Name":    "67",
        "X-Youtube-Client-Version": "1.20240101.00.00",
        "X-Goog-AuthUser":          "4",
        "X-Goog-Visitor-Id":        YT_VISITOR,
        "Authorization":            YT_AUTH,
        "Cookie":                   YT_COOKIE,
    }

def build_context():
    return {
        "client": {
            "clientName":    "WEB_REMIX",
            "clientVersion": "1.20240101.00.00",
            "hl":            "en",
            "gl":            "US",
        }
    }

def innertube_post(endpoint, body):
    url = f"{BASE_URL}/{endpoint}?key={API_KEY}&prettyPrint=false"
    resp = requests.post(url, json=body, headers=get_headers(), timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

# PASO 1: Buscar videoId
def search_video_id(title, artist):
    body = {
        "context": build_context(),
        "query":   f"{title} {artist}",
        "params":  "Eg-KAQwIARAAGAAgACgAMABqChAEEAMQCRAFEAo%3D"
    }
    data = innertube_post("search", body)

    try:
        tabs = (data["contents"]
                    ["tabbedSearchResultsRenderer"]
                    ["tabs"])
        for tab in tabs:
            shelf_list = (tab.get("tabRenderer", {})
                            .get("content", {})
                            .get("sectionListRenderer", {})
                            .get("contents", []))
            for section in shelf_list:
                items = (section.get("musicShelfRenderer", {})
                                .get("contents", []))
                for item in items:
                    video_id = (item.get("musicResponsiveListItemRenderer", {})
                                    .get("overlay", {})
                                    .get("musicItemThumbnailOverlayRenderer", {})
                                    .get("content", {})
                                    .get("musicPlayButtonRenderer", {})
                                    .get("playNavigationEndpoint", {})
                                    .get("watchEndpoint", {})
                                    .get("videoId"))
                    if video_id:
                        return video_id
    except Exception as e:
        print(f"[search] Error: {e}")
    return None

# PASO 2: Obtener browseId de lyrics
def get_lyrics_browse_id(video_id):
    body = {
        "context": build_context(),
        "videoId": video_id,
    }
    data = innertube_post("next", body)

    try:
        tabs = (data["contents"]
                    ["singleColumnMusicWatchNextResultsRenderer"]
                    ["tabbedRenderer"]
                    ["watchNextTabbedResultsRenderer"]
                    ["tabs"])
        for tab in tabs:
            tab_renderer = tab.get("tabRenderer", {})
            if tab_renderer.get("title", "").lower() == "lyrics":
                return (tab_renderer
                        .get("endpoint", {})
                        .get("browseEndpoint", {})
                        .get("browseId"))
    except Exception as e:
        print(f"[next] Error: {e}")
    return None

# PASO 3: Obtener lyrics desde browseId
def fetch_lyrics(browse_id):
    body = {
        "context":  build_context(),
        "browseId": browse_id,
    }
    data = innertube_post("browse", body)

    try:
        shelf = (data["contents"]
                     ["sectionListRenderer"]
                     ["contents"][0]
                     ["musicDescriptionShelfRenderer"])

        # Texto de las letras
        runs = shelf.get("description", {}).get("runs", [])
        lyrics_text = "".join(r.get("text", "") for r in runs)

        # Fuente (Musixmatch, LyricFind, etc.)
        source_runs = shelf.get("footer", {}).get("runs", [])
        source = "".join(r.get("text", "") for r in source_runs)

        return lyrics_text.strip() or None, source.strip() or None
    except Exception as e:
        print(f"[browse] Error: {e}")
    return None, None

# Endpoint principa
@app.route("/lyrics")
def get_lyrics():
    title  = request.args.get("title", "").strip()
    artist = request.args.get("artist", "").strip()

    if not title or not artist:
        return jsonify({"status": "error", "message": "title and artist required"}), 400

    try:
        # Paso 1
        video_id = search_video_id(title, artist)
        if not video_id:
            return jsonify({"status": "error", "message": f"No results for '{title}' by '{artist}'"}), 404

        # Paso 2
        browse_id = get_lyrics_browse_id(video_id)
        if not browse_id:
            return jsonify({"status": "error", "message": "No lyrics tab found"}), 404

        # Paso 3
        lyrics, source = fetch_lyrics(browse_id)
        if not lyrics:
            return jsonify({"status": "error", "message": "Lyrics unavailable"}), 404

        return jsonify({
            "status":  "success",
            "title":   title,
            "artist":  artist,
            "videoId": video_id,
            "lyrics":  lyrics,
            "source":  source,
        })

    except Exception as e:
        print(f"[/lyrics] Unexpected error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Health check
@app.route("/")
def index():
    return jsonify({"api": "ZyncWave-Lyrics", "status": "running"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
