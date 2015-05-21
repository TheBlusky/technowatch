from ConfigParser import SafeConfigParser
import json
from feedgen.feed import FeedGenerator
from bs4 import BeautifulSoup
from flask import Flask
import threading
import operator
import datetime
import requests
import pickle
import pytz
import time
import os


# Initialize app
app = Flask(__name__)

# Initialize feed
fg = FeedGenerator()

# Initialize conf
parser = SafeConfigParser()
parser.read(os.path.dirname(os.path.realpath(__file__)) + '/technowatch.conf')


def build():
    global fg
    fg = FeedGenerator()
    fg.title(parser.get('technowatch', 'name'))
    fg.language('en')
    fg.description(parser.get('technowatch', 'name'))
    fg.link(href=parser.get('technowatch', 'link'), rel='alternate')
    # Cleaning stories if too much
    if len(known_stories) > int(parser.get('technowatch', 'cache_max')):
        clean()
    # Sorting stories by crawled date
    for item in sorted(known_stories.values(), key=operator.itemgetter('crawledDate'), reverse=True):
        fe = fg.add_entry()
        fe.link(href=item['url'], rel='alternate')
        fe.title("[" + item['type'] + "] " + item['title'])
        fe.category({
            'label': item['type'],
            'term': item['type']
        })
        fe.author({'name': item['by']})
        fe.description(item['desc'])
        fe.pubdate(item['crawledDate'])
    # Caching RSS building
    fg.rss_file(os.path.dirname(os.path.realpath(__file__)) + '/static/rss.xml')
    pickle.dump(known_stories, open(os.path.dirname(os.path.realpath(__file__)) + "/technowatch.data", "wb"))

# Initialize global variable
try:
    known_stories = pickle.load(open(os.path.dirname(os.path.realpath(__file__)) + "/technowatch.data", "rb"))
except IOError:
    known_stories = {}
build()


def check_githubtrend():
    rebuild = False
    # requesting github + bs
    html_doc = requests.get('https://github.com/trending').content
    soup = BeautifulSoup(html_doc)
    for li in soup.find_all('li', {'class': 'repo-list-item'}):
        title = li.find("h3", {'class': 'repo-list-name'}).a.get('href')
        lang = li.find("p", {'class': 'repo-list-meta'}).get_text().split('\n')[1]
        if title not in known_stories:
            item = {'title': "[" + lang.replace(" ", "") + "] " + title,
                    'url': "https://github.com" + title,
                    'by': title.split("/")[1],
                    'crawledDate': datetime.datetime.now().replace(tzinfo=pytz.utc),
                    'type': "github",
                    'key': title,
                    'desc': li.find("p", {'class': 'repo-list-description'}).get_text()}
            known_stories[title] = item
            rebuild = True
    return rebuild

def check_producthunt():
    rebuild = False
    # requesting github + bs
    html_doc = requests.get('http://www.producthunt.com/').content
    soup = BeautifulSoup(html_doc)
    for li in soup.find_all('li', {'data-react-class': 'PostItem'})[:10]:
        j = json.loads(li.get('data-react-props'))
        key = "ph-" + str(j['id'])
        if key not in known_stories:
            item = {'title': j['name'],
                    'url': "http://www.producthunt.com" + j['shortened_url'],
                    'by': 'no one',
                    'crawledDate': datetime.datetime.now().replace(tzinfo=pytz.utc),
                    'type': "producthunt",
                    'key': key,
                    'desc': j['tagline']}
            known_stories[key] = item
            rebuild = True
    return rebuild


def check_hackernews():
    rebuild = False
    # API request for top stories
    top = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json') \
              .json()[:int(parser.get('technowatch', 'hackernews_noise'))]
    for story in top:
        if story not in known_stories:
            # Getting and storing new top story information
            item = requests.get('https://hacker-news.firebaseio.com/v0/item/' + str(story) + '.json').json()
            item['crawledDate'] = datetime.datetime.now().replace(tzinfo=pytz.utc)
            item['type'] = "hacker-news"
            item['key'] = story
            item['desc'] = item['title'] + " <br /> " + item['url']
            known_stories[story] = item
            rebuild = True
    return rebuild


def check_news():
    rebuild = False
    # Checking all new news
    rebuild = True if check_hackernews() else rebuild
    rebuild = True if check_githubtrend() else rebuild
    rebuild = True if check_producthunt() else rebuild
    if rebuild:
        # If new stories, rebuilding feed
        build()


def clean():
    left = len(known_stories) - int(parser.get('technowatch', 'cache_min'))
    for item in sorted(known_stories.values(), key=operator.itemgetter('crawledDate')):
        del known_stories[item.key]
        left -= 1
        if left == 0:
            return


def threaded():
    while True:
        check_news()
        time.sleep(int(parser.get('technowatch', 'refresh')))


@app.route('/')
def show_rss():
    # Simply return cached RSS
    return app.send_static_file('rss.xml')


if __name__ == '__main__':
    thread = threading.Thread(None, threaded, None)
    thread.start()
    app.run(host=parser.get('technowatch', 'host'), port=int(parser.get('technowatch', 'port')))
