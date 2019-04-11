import requests
from bs4 import BeautifulSoup as bs
from social_analysis import link_report


def word_counter(soup):
    text = (' ').join([x.text for x in soup.find("div", {"class": "story_body"}).find_all("p")])
    words = len(text.split())
    length = words/265
    return {"time_to_read": round(length, 2),
            "words": words}


def byline(soup):
    from pymongo import MongoClient
    import settings
    db = MongoClient(settings.MONGODB_URI).get_database()
    authors = soup.find("p", {"byline"}).find_all("a")
    if authors:
        author_names = [x.text for x in authors]
    bylines = []
    text = f'This story was written by'
    for x in author_names:
        na = db.authors.find_one({"name": x})
        if na['twitter']:
            by = na['twitter']
        else:
            by = x
        bylines.append({"name": by, "articles": na['articles']})
    if len(author_names) == 2:
        text = f'This story was written by '
        for x in bylines:
            text += f'{x["name"]}'
            if x is not bylines[-1]:
                text += ' and '
            else:
                text += '.'
    else:
        text = f'This story was written by {x["name"]}, who has written {x["articles"]} for @texastribune.'
    return {"byline": text}


def href_stats(soup):
    body = soup.find("div", {"class": "story_body"}).find_all("p")
    junk_links = ['https://mediakit.texastribune.org/']
    story_links = []
    external_links = []
    context_links = []
    for p in body:
        hs = p.find_all("a")
        if hs:
            for x in hs:
                if 'texastribune' in x['href'] and x['href'] not in junk_links:
                    if x['href'].startswith('https://www.texastribune.org/directory/'):
                        context_links.append(x['href'])
                    else:
                        story_links.append(x['href'])
                else:
                    if x['href'] not in junk_links:
                        external_links.append(x['href'])
    return {"story_links": len(story_links),
            "external_links": len(external_links),
            "context_links": len(context_links)}


def tribune_stats(soup, url):
    imgs = soup.find_all("figure")
    images = len(imgs)
    original_images = 0
    try:
        videos = len(soup.find_all("div", {"class": "js-video-container"}))
    except AttributeError:
        videos = 0
    try:
        documents = len(soup.find("div", {"plugin-document"}).find_all("li"))
    except AttributeError:
        documents = 0

    # This is imperfect. But it searchs for credits on the images.
    for x in soup.find_all("cite"):
        if "Texas Tribune" in x.text:
            original_images += 1

    # Adds basic stats
    info = {"images": images,
            "original_images": original_images,
            "videos": videos,
            "documents": documents}

    # Adds basic count article length
    info.update(word_counter(soup))

    # Adds "transparency indicators"
    info.update(transparency_finder(soup))

    # Adds analysis of links:
    info.update(href_stats(soup))

    # Adds byline stats:
    info.update(byline(soup))

    # Adds social info:
    info.update(social_data(url))

    # Returns everything
    return info


def transparency_finder(soup):
    info = {"correction": False, "disclosure": False}
    if soup.find("sub"):
        if 'Correction' in soup.find("sub"):
            info['correction'] = True
    return info


def social_data(url):
    l = link_report('https://www.texastribune.org/2019/04/11/texas-legislature-property-tax-debate-school-districts/')
    data = []
    for x in l:
        if x['name'] == 'Texas Tribune' or x['platform'] != 'Twitter':
            continue
        else:
            data.append(x['link'].split('/')[3])
            if len(data) > 4:
                return data
    text = 'This story was shared by '
    for d in data:
        text += f'@{d}'
        if d != data[-1]:
            text += ', '
    text += ', among others.'

    return {"social_copy": text}


def link_check(url):
    soup = bs(requests.get(url).content, "html.parser")
    data = tribune_stats(soup, url)
    return data
