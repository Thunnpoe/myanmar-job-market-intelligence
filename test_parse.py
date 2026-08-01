import requests
from bs4 import BeautifulSoup


url = "https://www.jobnet.com.mm/job/data-engineer-cb-bank/133661"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)

soup = BeautifulSoup(response.text, "lxml")

html = str(soup)


keyword = "Experience level"

position = html.find(keyword)

print(html[position-1000:position+2000])