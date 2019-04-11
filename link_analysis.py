import requests
from bs4 import BeautifulSoup as bs


def word_counter(soup):
    text = (' ').join([x.text for x in soup.find("div", {"class": "story_body"}).find_all("p")])
    words = len(text.split())
    length = words/265
    return {"time_to_read": round(length, 2),
            "words": words}


def tribune_stats(soup):
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

    # Returns everything
    return info


def transparency_finder(soup):
    info = {"correction": False, "disclosure": False}
    if soup.find("sub"):
        if 'Correction' in soup.find("sub"):
            info['correction'] = True
    return info


def link_check(url):
    soup = bs(requests.get(url).content, "html.parser")
    data = tribune_stats(soup)
    return data
