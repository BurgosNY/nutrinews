from urllib.parse import urlparse
import requests
import settings
from tweepy import TweepError
import tweepy
import time
import pendulum


def crowdtangle_data(url, token):
    api_url = f'https://api.crowdtangle.com/links'
    query = {'link': clean_url(url), 'token': token}
    response = requests.get(api_url, params=query)
    return response.json()


def crowd_twitter(ct_post, twitterbot, url):
    user = twitterbot.get_user(ct_post['account']['platformId'])
    try:
        tweet = twitterbot.read_status(
            twitterbot._api.get_status(ct_post['platformId']), url)
    except TweepError:
        tweet = {"favorite_count": 0, "retweet_count": 0,
                 "id_str": str(ct_post['platformId'])}
    tweet_link = f'https://twitter.com/{user["screen_name"]}/status/{tweet["id_str"]}'
    interactions = tweet['favorite_count'] + tweet['retweet_count']
    info = {"link": tweet_link, "interactions": interactions,
            "subscriberCount": user['followers_count'],
            "image": user['profile_image_url'],
            "name": user['name'], "verified": user["verified"],
            "platform": "Twitter"}
    return info


def crowd_facebook(ct_post):
    info = {"image": ct_post['account']['profileImage'],
            "interactions": sum(ct_post['statistics']['actual'].values()),
            "link": ct_post['postUrl'],
            "name": ct_post['account']['name'],
            "subscriberCount": ct_post['account']['subscriberCount'],
            "verified": ct_post['account']['verified'],
            "platform": "Facebook"
            }
    return info


def crowd_reddit(ct_post):
    info = {"image": 'https://en.wikipedia.org/wiki/File:Reddit.svg',
            "interactions": sum(ct_post['statistics']['actual'].values()),
            "link": ct_post['postUrl'],
            "name": f"r/{ct_post['account']['name']}",
            "subscriberCount": ct_post['subscriberCount'],
            "verified": ct_post['account']['verified'],
            "platform": "Reddit"
            }
    return info


def link_report(url):
    twitterbot = TwitterBot(settings.TWITTER_ACCESS_TOKEN,
                            settings.TWITTER_ACCESS_TOKEN_SECRET,
                            settings.TWITTER_CONSUMER_KEY,
                            settings.TWITTER_CONSUMER_SECRET)
    ctd = crowdtangle_data(url, settings.CROWDTANGLE_TOKEN)
    posts = []
    for post in ctd['result']['posts']:
        if post['platform'] == 'Twitter':
            posts.append(crowd_twitter(post, twitterbot, url))
        elif post['platform'] == 'Facebook':
            posts.append(crowd_facebook(post))
        elif post['platform'] == 'Reddit':
            posts.append(crowd_reddit(post))
    return sorted(posts, key=lambda k: k['interactions'], reverse=True)


def parse_tweet_url(tweet_json):
    try:
        url = tweet_json['entities']['urls'][0]['expanded_url']
        cleaned_url = url.split('?')[0]
    except IndexError:
        cleaned_url = 'https://www.twitter.com'
    return cleaned_url


class TwitterBot:

    'Simple class to Interact with the Twitter API'

    def __init__(self, access_token, access_token_secret,
                 consumer_key, consumer_secret):
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self._api = tweepy.API(auth)

    def search(self, link, since_id=None):
        search_link = link.split('://')[1]
        response = tweepy.Cursor(
            self._api.search,
            q=search_link,
            rpp=100,
            since_id=since_id,
        )

        # TODO: collect tweepy.error.TweepError error
        for page in response.pages():
            for status in page:
                    yield self.read_status(status, link)
            time.sleep(6)

    def read_status(self, status, search_url):
        # A better way to process Tweepy individual results
        nt = status._json
        new_twitter_user = dict(
            description=nt['user']['description'],
            followers_count=nt['user']['followers_count'],
            friends_count=nt['user']['friends_count'],
            id_str=nt['user']['id_str'],
            location=nt['user']['location'],
            name=nt['user']['name'],
            screen_name=nt['user']['screen_name'],
            verified=nt['user']['verified'],
        )
        new_tweet = dict(
            id_str=nt['id_str'],
            favorite_count=nt['favorite_count'],
            text=nt['text'],
            retweeted=nt['retweeted'],
            retweet_count=nt['retweet_count'],
            link_url=parse_tweet_url(nt),
            fake_news_url=search_url,
            user=new_twitter_user
        )
        return new_tweet

    def get_user(self, user_id):
        data = self._api.get_user(id=user_id)._json
        profile_image_url = data['profile_image_url'].replace('_normal', '')
        info = {"description": data['description'],
                "followers_count": data['followers_count'],
                "id_str": data['id_str'],
                "name": data['name'],
                "profile_image_url": profile_image_url,
                "screen_name": data['screen_name'],
                "verified": data['verified']
                }
        return info

    def get_latest_posts(self, user_name):
        timeline = self._api.user_timeline(user_name, include_entities=True,                               tweet_mode='extended')
        posts = []
        for tweet in timeline:
            urls = tweet._json['entities']['urls']
            posts.append(urls[0]['expanded_url'])
        return posts


def clean_url(url):
    """Remove querystring and fragments from URL"""

    parsed = urlparse(url)
    params = f';{parsed.params}' if parsed.params else ''
    return f'{parsed.scheme}://{parsed.netloc}{parsed.path}{params}'
