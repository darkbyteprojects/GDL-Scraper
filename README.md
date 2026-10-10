# GDL Scraper | [![GDL Builder](https://github.com/darkbyteprojects/GDL-Scraper/actions/workflows/sync.yml/badge.svg)](https://github.com/darkbyteprojects/GDL-Scraper/actions/workflows/sync.yml)

An automated live stream catalog and token-resolution scraper. The dataset is refreshed via GitHub Actions to maintain valid HMAC authentication sessions and token signatures for MPEG-DASH and HLS playback.

---

## 📖 Scraper Documentation & Response Schemas

<br>

### 1. Resolved Streams Endpoint (<code>jiotv_resolved_streams.json</code>)

Returns the complete catalog with all alternative video sources, active session tokens, Widevine DRM key arrays, and proxy routing targets.

<details>
<summary>Schema Overview</summary>

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

</details>

<details>
<summary>Response Example</summary>

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
    }
  ]
}
```

</details>

</details>

### 2. Base Catalog Endpoint (<code>jiotv_channels.json</code>)

Clean list of all indexed channels without dynamic tokens. Useful for quick catalog rendering and client-side searching.

<details>
<summary>Response Example</summary>

```json
{
  "name": "Channel Name",
  "slug": "channel-name",
  "category": "CategoryName",
  "language": "en",
  "logo": "https://example.com/image.png"
}
```

</details>

### 3. Service Metadata Endpoint (<code>gdl_app_metadata.json</code>)

Provides underlying infrastructure URLs, push service identifiers, and global channel counts.

<details>
<summary>Response Example</summary>

```json
{
  "site_info": {
    "api_base": "https://example.com",
    "frontend_url": "https://example.com",
    "gateway_url": "https://example.com",
    "push_service": {
      "api_url": "https://example.com",
      "website_id": "XXXXXXX"
    }
  },
  "total_channels": XXXX
}
```

</details>

## ⚙️ Running Locally

<br>

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

</details>

## 🌟 Support & Feedback

- **Give a Star:** If you find this repository useful, please leave a **⭐ Star** to support the project and keep it alive!
- **Report Issues:** If you have any issue, open an issue under the [Issues](../../issues) tab.

---

<p align="center">
  <i>Made with ❤️ by <b>DarkByteProjects</b></i>
</p>
