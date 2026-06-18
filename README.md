# ZyncWave-Lyrics

Servidor minimalista para obtener letras de YouTube Music via Innertube API autenticado.
Usado internamente por ZyncWave Android music player.

## Endpoint

```
GET /lyrics?title=Yesterday&artist=The+Beatles
```

### Respuesta exitosa
```json
{
  "status": "success",
  "title": "Yesterday",
  "artist": "The Beatles",
  "videoId": "Ztdc7TcPdAA",
  "lyrics": "Yesterday\nAll my troubles seemed so far away...",
  "source": "Source: Musixmatch"
}
```

## Variables de entorno requeridas

| Variable | Descripción |
|----------|-------------|
| `YT_COOKIE` | Cookies de sesión de YouTube Music |
| `YT_AUTH` | Header Authorization de YouTube Music |
| `YT_VISITOR_ID` | Header X-Goog-Visitor-Id de YouTube Music |

## Deploy en Render

1. Fork este repo
2. Nuevo Web Service en Render → conectar repo
3. Runtime: Docker
4. Agregar variables de entorno
5. Deploy
