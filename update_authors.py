import requests
from pymongo import MongoClient
from bs4 import BeautifulSoup as bs
import settings


def find_twitter_handle(author_soup):
    for x in author_soup.find_all("a"):
        if x['href']:
            if 'twitter' in x['href'] and len(x.text) > 2:
                return x.text.strip()
    return None


def get_number_articles(staff_page):
    if 'about' not in staff_page:
        return 0
    r = requests.get(staff_page)
    soup = bs(r.content, "html.parser")
    try:
        pages = int(soup.find("li", {"class": "col_inline hide_until--m page last"}).text)
    except AttributeError:
        return 0
    # Links per page: 15
    last_page = f'{staff_page}?page={pages}'
    soup2 = bs(requests.get(last_page).content, "html.parser")
    articles = (pages-1)*15 + len(soup2.find_all('h3', {'class': 'headline'}))
    return articles


def author_data(author_soup):
    info = {}
    info['thumbnail'] = author_soup.find("a")['href']
    try:
        info['title'] = author_soup.find("div", {"class": "byline"}).title()
    except TypeError:
        info['title'] = None
    author_page = author_soup.find_all("a")[-1]['href']
    author = f'https://www.texastribune.org{author_page}'
    info['articles'] = get_number_articles(author)
    info['author_page'] = author
    info['name'] = author_soup.find("h2").text
    info['twitter'] = find_twitter_handle(author_soup)
    return info


def main():
    db = MongoClient(settings.MONGODB_URI).get_default_database()

    r = requests.get('https://www.texastribune.org/about/staff/')
    soup = bs(r.content, "html.parser")
    authors = soup.find_all("section", {"class": "bio"})
    for a in authors:
        info = author_data(a)
        db.authors.insert_one(info)
    print('Done!')


if __name__ == '__main__':
    main()
