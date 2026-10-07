import concurrent.futures
import json
import os
import time
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_BASE = "https://api.freeforall.dev"
PERMANENT_GATEWAY = "https://play.freeforall.dev"

# Dedicated Session with connection pooling
session = requests.Session()
retries = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    raise_on_status=False,
)
adapter = HTTPAdapter(
    max_retries=retries, 
    pool_connections=25, 
    pool_maxsize=25
)
session.mount("https://", adapter)
session.mount("http://", adapter)


def resolve_dynamic_frontend_url():
    """
    Follows the permanent gateway's redirect to automatically obtain
    the currently active frontend mirror domain on every run.
    """
    print(f"--- [Step 0: Detecting Active Frontend via {PERMANENT_GATEWAY}] ---")
    try:
        r = session.get(
            PERMANENT_GATEWAY,
            allow_redirects=True,
            timeout=10,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            },
        )
        detected_url = r.url.rstrip("/")
        # If redirected to a subpath like /browse or /watch, strip down to the domain root
        from urllib.parse import urlparse
        parsed = urlparse(detected_url)
        clean_origin = f"{parsed.scheme}://{parsed.netloc}"
        print(f"Active Frontend Detected: {clean_origin}\n")
        return clean_origin
    except Exception as e:
        print(f"[!] Warning: Could not trace gateway redirect ({e}), using API base as fallback.")
        return API_BASE


def build_headers(frontend_url):
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Origin": frontend_url,
        "Referer": f"{frontend_url}/",
    }


def to_absolute_url(url_str):
    """Expands relative proxy routes into full absolute URLs."""
    if not url_str or not isinstance(url_str, str):
        return url_str
    if url_str.startswith("/"):
        return urljoin(API_BASE, url_str)
    return url_str


def sync_channels_and_metadata(catalog_path, metadata_path, headers, active_frontend):
    """Fetches channel catalog and saves fresh metadata with the resolved frontend URL."""
    print("--- [Step 1: Syncing Fresh Channel Catalog from API] ---")
    fresh_channels = {}
    page = 1
    total_pages = 1
    total_channels_count = 0

    while page <= total_pages:
        try:
            res = session.get(
                f"{API_BASE}/api/jiotv/channels?page={page}",
                headers=headers,
                timeout=18,
            )
            if res.status_code != 200:
                print(f"[!] Warning: Page {page} returned status {res.status_code}")
                break

            data = res.json()
            if page == 1:
                total_pages = data.get("total_pages", 1)
                total_channels_count = data.get("total", "unknown")
                print(f"Found {total_channels_count} channels across {total_pages} catalog pages.")

            for ch in data.get("channels", []):
                slug = ch.get("slug")
                if slug:
                    fresh_channels[slug] = {
                        "name": ch.get("name"),
                        "slug": slug,
                        "category": ch.get("category"),
                        "language": ch.get("language"),
                        "logo": ch.get("logo"),
                    }

            print(f"Catalog page {page}/{total_pages} downloaded.")
            page += 1
            time.sleep(0.04)
        except Exception as e:
            print(f"[!] Error fetching catalog page {page}: {e}")
            break

    # Save metadata with the automatically updated frontend URL
    metadata_content = {
        "site_info": {
            "api_base": API_BASE,
            "frontend_url": active_frontend,
            "gateway_url": PERMANENT_GATEWAY,
            "push_service": {
                "api_url": "https://notification.gdls.me",
                "website_id": "LX6O1O00K",
            },
        },
        "total_channels": total_channels_count,
    }

    with open(metadata_path, "w", encoding="utf-8") as mf:
        json.dump(metadata_content, mf, ensure_ascii=False, indent=4)
    print(f"Fresh metadata saved to '{metadata_path}'.")

    channel_list = list(fresh_channels.values())
    with open(catalog_path, "w", encoding="utf-8") as cf:
        json.dump(channel_list, cf, ensure_ascii=False, indent=4)
    print(f"Saved {len(channel_list)} channels to '{catalog_path}'.\n")

    return channel_list


def fetch_all_channel_streams(slug, headers):
    """Finds all stream instances for a channel."""
    candidate_urls = [
        f"{API_BASE}/api/channels/{slug}/streams",
        f"{API_BASE}/api/channel/{slug}/streams",
        f"{API_BASE}/api/channels/{slug}",
        f"{API_BASE}/api/channel/{slug}",
    ]

    discovered = {}

    for url in candidate_urls:
        try:
            resp = session.get(url, headers=headers, timeout=12)
            if resp.status_code == 200:
                payload = resp.json()
                items = []

                if isinstance(payload, list):
                    items = payload
                elif isinstance(payload, dict):
                    items = payload.get("streams", [])

                for item in items:
                    st_id = item.get("id") or item.get("stream_id")
                    if st_id and st_id not in discovered:
                        discovered[st_id] = item

                if len(discovered) > 0:
                    break
        except Exception:
            continue

    return list(discovered.values())


def resolve_single_stream(slug, stream, headers):
    """Resolves stream URLs with proper timeouts."""
    stream_id = stream.get("id") or stream.get("stream_id")
    stream_name = stream.get("name") or stream.get("title", f"Stream {stream_id}")

    if not stream_id:
        return None

    resolve_url = f"{API_BASE}/api/channels/{slug}/streams/{stream_id}/resolve"
    for attempt in range(2):
        try:
            res = session.get(resolve_url, headers=headers, timeout=18)
            if res.status_code == 200:
                data = res.json()

                if isinstance(data, dict):
                    playback_url = (
                        data.pop("resolved_url", None)
                        or data.pop("url", None)
                        or data.pop("stream_url", None)
                    )

                    if data.get("proxy_url"):
                        data["proxy_url"] = to_absolute_url(data["proxy_url"])
                    if data.get("license_proxy_url"):
                        data["license_proxy_url"] = to_absolute_url(data["license_proxy_url"])

                    return {
                        "stream_id": stream_id,
                        "stream_name": stream_name,
                        "stream_url": playback_url,
                        "details": data,
                    }
                else:
                    return {
                        "stream_id": stream_id,
                        "stream_name": stream_name,
                        "stream_url": str(data),
                        "details": {},
                    }
            elif res.status_code == 429:
                time.sleep(1.0)
        except Exception:
            time.sleep(0.3)

    return None


def process_channel(ch, headers):
    """Processes all streams for a given channel."""
    slug = ch.get("slug")
    raw_streams = fetch_all_channel_streams(slug, headers)
    resolved_streams = []

    for st in raw_streams:
        resolved = resolve_single_stream(slug, st, headers)
        if resolved and resolved.get("stream_url"):
            resolved_streams.append(resolved)

    return {
        "name": ch.get("name"),
        "slug": slug,
        "category": ch.get("category"),
        "language": ch.get("language"),
        "logo": ch.get("logo"),
        "streams_count": len(resolved_streams),
        "streams": resolved_streams,
    }


def run_pipeline(workers=8):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    catalog_file = os.path.join(base_dir, "jiotv_channels.json")
    resolved_file = os.path.join(base_dir, "jiotv_resolved_streams.json")
    metadata_file = os.path.join(base_dir, "gdl_app_metadata.json")

    # Step 0: Resolve active frontend URL via permanent redirect gateway
    active_frontend = resolve_dynamic_frontend_url()
    headers = build_headers(active_frontend)

    # Step 1: Refresh channels & write fresh metadata
    channels = sync_channels_and_metadata(catalog_file, metadata_file, headers, active_frontend)

    total = len(channels)
    print(f"--- [Step 2: Resolving Streams for {total} Channels ({workers} Stable Workers)] ---")

    results = []
    completed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_ch = {executor.submit(process_channel, ch, headers): ch for ch in channels}

        for future in concurrent.futures.as_completed(future_to_ch):
            completed += 1
            ch_data = future_to_ch[future]
            try:
                res = future.result()
                results.append(res)
                print(f"[{completed}/{total}] Done: {res['name']} ({res['streams_count']} streams)")
            except Exception as e:
                print(f"[{completed}/{total}] Failed: {ch_data.get('name')}: {e}")

            # Auto-save progress every 50 channels
            if completed % 50 == 0 or completed == total:
                with open(resolved_file, "w", encoding="utf-8") as out:
                    json.dump(results, out, ensure_ascii=False, indent=4)
                print(f"\n>>> Progress saved ({completed}/{total}) to disk.\n")

    print(f"\nCompleted! All resolved streams written to '{resolved_file}'.")


if __name__ == "__main__":
    run_pipeline(workers=8)
