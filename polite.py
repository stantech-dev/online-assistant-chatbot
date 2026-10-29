import time

import requests

HEADERS = {"User-Agent": "GINT-AU-Assistant/0.1 (contact: gint.ai.af@gmail.com)"}
CRAWL_DELAY = 10  # seconds; au.ac.ke/robots.txt asks for this

_last_request = 0.0
_session = requests.Session()
_session.headers.update(HEADERS)


def polite_get(url, retries=3, **kwargs):
    """GET that always waits out the crawl delay and retries gently on network errors."""
    global _last_request
    for attempt in range(1, retries + 1):
        wait = CRAWL_DELAY - (time.time() - _last_request)
        if wait > 0:
            time.sleep(wait)
        _last_request = time.time()
        try:
            r = _session.get(url, timeout=60, **kwargs)
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as e:
            # A clear HTTP answer below 500 (404, 429...) means "don't retry"
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status is not None and status < 500:
                raise
            if attempt == retries:
                raise
            backoff = 30 * attempt
            print(f"  network problem ({type(e).__name__}); retrying in {backoff}s")
            time.sleep(backoff)