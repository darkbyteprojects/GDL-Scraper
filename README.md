# GDL Scraper

An automated live stream catalog and token-resolution scraper. The dataset is refreshed via GitHub Actions to maintain valid HMAC authentication sessions and token signatures for MPEG-DASH and HLS playback.

---

## 🚀 Live Raw Endpoints (GitHub Raw)

You can consume these endpoints directly in any web player, IPTV player, or backend service via raw URLs:

| Resource | Direct Raw URL |
| :--- | :--- |
| **All Resolved Streams** | `https://raw.githubusercontent.com/darkbyteprojects/GDL-Scraper/main/jiotv_resolved_streams.json` |
| **Channel Catalog** | `https://raw.githubusercontent.com/darkbyteprojects/GDL-Scraper/main/jiotv_channels.json` |
| **Service Metadata** | `https://raw.githubusercontent.com/darkbyteprojects/GDL-Scraper/main/gdl_app_metadata.json` |

---

## 📖 Scraper Documentation & Response Schemas

### 1. Resolved Streams Endpoint (`jiotv_resolved_streams.json`)

Returns the complete catalog with all alternative video sources, active session tokens, Widevine DRM key arrays, and proxy routing targets.

#### Schema Overview

- `name` *(string)*: Display name of the channel.
- `slug` *(string)*: Unique URL-safe identifier for the channel.
- `category` *(string)*: Broadcast genre.
- `language` *(string)*: Primary audio language code or identifier.
- `logo` *(string)*: Direct link to the high-resolution channel badge image.
- `streams_count` *(integer)*: Total available alternative stream variants.
- `streams` *(array)*:
  - `stream_id` *(integer)*: Stream identifier.
  - `stream_name` *(string)*: Stream title or quality profile label.
  - `stream_url` *(string)*: Resolved playback URL (`.mpd` or `.m3u8`) with active `__hdnea__` access token.
  - `details` *(object)*:
    - `needs_proxy` *(boolean)*: Indicates if regional or CORS bypassing proxy is required.
    - `headers` *(object | null)*: Required HTTP request headers (e.g., `User-Agent`, `Referer`) for playback.
    - `drm_key` *(array | null)*: List of Widevine Key ID (`kid`) and Encryption Key (`key`) pairs.
    - `license_key_url` *(string | null)*: Remote license server for DRM handshakes.
    - `proxy_url` *(string | null)*: Absolute URL to the stream proxy server if proxying is required.
    - `license_proxy_url` *(string | null)*: Absolute URL for proxied license key acquisition.
    - `jio` *(boolean)*: Whether the source stream is an official Jio CDN endpoint.
    - `cached` *(boolean)*: Indicates if the URL was resolved via backend cache.

#### Response Example

```json
  {
    "name": "Channel Name",
    "slug": "channel-name",
    "category": "CategoryName",
    "language": "en",
    "logo": "https://example.com/image.png",
    "streams_count": X,
    "streams": [
      {
        "stream_id": xxxxxx,
        "stream_name": "Stream xxxxxx",
        "stream_url": "https://example.com/stream.mpd",
        "details": {
          "needs_proxy": true/false,
          "headers": null,
          "drm_key": [
            {
              "kid": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
              "key": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            }
          ],
          "license_key_url": "https://example.com/key?id=XXX",
          "jio": true/false,
          "cached": true/false,
          "proxy_url": "https://example.com",
          "license_proxy_url": "https://example.com/proxy?resource=abcd"
        }
      },
    ]
  }
````

### 2. Base Catalog Endpoint (`jiotv_channels.json`)
Clean list of all indexed channels without dynamic tokens. Useful for quick catalog rendering and client-side searching.

#### Response Example

````json
  {
    "name": "Channel Name",
    "slug": "channel-name",
    "category": "CategoryName",
    "language": "en",
    "logo": "https://exapmle.com/image.png"
  },
````

### 3. Service Metadata Endpoint (`gdl_app_metadata.json`)
Provides underlying infrastructure URLs, push service identifiers, and global channel counts.

#### Response Example

````json
  {
    "site_info": {
      "api_base": "https://example.com",
      "frontend_url": "https://example.com",
      "push_service": {
        "api_url": "https://example.com",
        "website_id": "XXXXXXX"
      }
    },
    "total_channels": XXXX
  }
````

## ⚙️ Running Locally

1. Clone repository:
```bash
git clone https://github.com/darkbyteprojects/GDL-Scraper.git
```
```bash
cd GDL-Scraper
```
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Run pipeline manually:
```bash
python gdl_full_scraper.py
```
