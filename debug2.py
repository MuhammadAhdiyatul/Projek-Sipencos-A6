import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "id-ID,id;q=0.9",
}

r = requests.get("https://www.sewakost.com/kost/bandung", headers=HEADERS, timeout=20)
soup = BeautifulSoup(r.text, "html.parser")

# Tampilkan semua link yang mengandung /kost/bandung/
links = soup.select("a[href*='/kost/bandung/']")
print(f"Total link ditemukan: {len(links)}")
for a in links[:20]:
    print(a.get("href"))