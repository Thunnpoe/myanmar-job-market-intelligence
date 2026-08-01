import requests

url = "https://www.jobnet.com.mm/job/data-engineer-cb-bank/133661"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)

html = response.text


keyword = 'job-details__card-title2'

position = html.find(keyword)

print(html[position-1000:position+500])