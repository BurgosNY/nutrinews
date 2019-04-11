import requests
from bs4 import BeautifulSoup as bs


r = requests.get('https://www.texastribune.org/about/staff/')
soup = bs(r.content, "html.parser")


def find_name(author_soup):
    for x in author_soup.find_all("a"):
        if x['href']:
            if 'twitter' in x['href'] and len(x.text) > 2:
                return x.text.strip()
    return None
