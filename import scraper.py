import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

url = "https://www.okinawa-ct.ac.jp/campus_life/dormitories/usual/"
res = requests.get(url)
res.raise_for_status()

soup = BeautifulSoup(res.text, "html.parser")
pdf_link = soup.find("a", string=lambda t: t and "寮食献立表" in t)
pdf_url = urljoin(url, pdf_link.get("href"))

pdf_res = requests.get(pdf_url)
with open("menu.pdf", "wb") as f:
    f.write(pdf_res.content)
