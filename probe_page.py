from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "GINT-AU-Assistant/0.1 (contact: your-email@example.com)"}

URLS = [
    "https://au.ac.ke/au-programmes/",
    "https://au.ac.ke/admission-documents/",
    "https://au.ac.ke/student-downloads/",
    "https://au.ac.ke/au-downloads/",
    "https://au.ac.ke/unit-registration-procedure/",
    "https://au.ac.ke/student-welfare-services/",
    "https://au.ac.ke/hostels-booking/",
    "https://au.ac.ke/scholarships/",
    "https://au.ac.ke/new-student-registration-admission-process/",
    "https://au.ac.ke/notice-for-students-special-and-supplementary-exams/",
    "https://au.ac.ke/fee-clearance-reminder/",
    "https://au.ac.ke/school-of-sste/",
    "https://au.ac.ke/school-of-education-and-social-sciences/",
    "https://au.ac.ke/school-of-health-sciences/",
    "https://au.ac.ke/school-of-business-economics-and-human-resource-development/",
    "https://au.ac.ke/ict/",
    "https://au.ac.ke/post-graduate/",
    "https://au.ac.ke/tvet-institute-directorate/",
]

# Always check what the site owner asks crawlers to avoid
r = requests.get("https://au.ac.ke/robots.txt", headers=HEADERS, timeout=30)
print("robots.txt status:", r.status_code)
print(r.text[:600], "\n")


def main_text(soup):
    for tag in soup(["script", "style", "noscript", "nav", "footer", "form"]):
        tag.decompose()
    container = soup.find("main") or soup.find("article") or soup.body
    return " ".join(container.get_text(" ").split())


for url in URLS:
    print("=" * 80)
    print(url)
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
    except Exception as e:
        print("  FAILED:", e)
        continue
    soup = BeautifulSoup(r.text, "html.parser")
    pdfs = sorted({
        urljoin(url, a["href"])
        for a in soup.find_all("a", href=True)
        if a["href"].lower().split("?")[0].endswith(".pdf")
    })
    text = main_text(soup)
    print(f"  status {r.status_code}, page text: {len(text)} chars, PDF links: {len(pdfs)}")
    print("  preview:", text[:250])
    for p in pdfs[:8]:
        print("  PDF:", p)