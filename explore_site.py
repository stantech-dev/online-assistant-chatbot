"""Explores and checks for client's website pages holding useful data
   NOTE: Only works if the website is WordPress"""
import csv
import html

import requests
from bs4 import BeautifulSoup

BASE = "https://au.ac.ke/wp-json/wp/v2"
HEADERS = {"User-Agent": "GINT-AU-Assistant/0.1 (contact: gint.ai.af@gmail.com)"}


def fetch_all(kind):
    """Fetch every published page or post (GET requests only)."""
    items, page = [], 1
    while True:
        r = requests.get(
            f"{BASE}/{kind}",
            params={"per_page": 50, "page": page,
                    "_fields": "id,link,title,modified,content"},
            headers=HEADERS,
            timeout=30,
        )
        if r.status_code == 400:   # WordPress answers 400 when you go past the last page
            break
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        items.extend(batch)
        if page >= int(r.headers.get("X-WP-TotalPages", 1)):
            break
        page += 1
    return items


def html_to_text(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return " ".join(soup.get_text(" ").split())


rows = []
for kind in ["pages", "posts"]:
    items = fetch_all(kind)
    print(f"\n=== {kind}: {len(items)} found ===")
    items.sort(key=lambda x: x["modified"], reverse=True)

    for it in items:
        title = html.unescape(it["title"]["rendered"])
        text_len = len(html_to_text(it["content"]["rendered"]))
        rows.append([kind, it["id"], it["modified"][:10], text_len, title, it["link"]])

    for kind_, _id, modified, text_len, title, link in [r for r in rows if r[0] == kind][:60]:
        print(f"{modified}  {text_len:6d} chars  {title[:45]:45}  {link}")

with open("site_inventory.csv", "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerow(["type", "id", "modified", "text_chars", "title", "link"])
    csv.writer(f).writerows(rows)

print(f"\nSaved all {len(rows)} entries to site_inventory.csv")