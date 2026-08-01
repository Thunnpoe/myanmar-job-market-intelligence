import requests
from bs4 import BeautifulSoup

url = "https://www.jobnet.com.mm/jobs?kw=data+engineer"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")

links = []

for a in soup.find_all("a", href=True):
    href = a["href"]
    if "/job/" in href:
        links.append(href)

print("Total job links found:", len(set(links)))

for link in sorted(set(links)):
    print(link)