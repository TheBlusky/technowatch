from ConfigParser import SafeConfigParser
import json
from feedgen.feed import FeedGenerator
from bs4 import BeautifulSoup
import threading
import operator
import datetime
import requests
import pickle
import pytz
import time
import os


# Initialize conf
cust_path = os.path.dirname(os.path.realpath(__file__))
parser = SafeConfigParser()
parser.read(cust_path + '/technowatch.conf')

# Initialize feed
fg = FeedGenerator()

# Initialize app
if parser.get('wsgi', 'activated') == "True":
    from flask import Flask
    app = Flask(__name__)


def upload():
    from ftplib import FTP
    print "Uploading ..."
    ftp = FTP(parser.get('ftp', 'host'),
              parser.get('ftp', 'user'),
              parser.get('ftp', 'pass'))
    ftp.cwd(parser.get('ftp', 'path'))
    fg.rss_file(cust_path + '/static/' + parser.get('ftp', 'filename'))
    ftp.storbinary("STOR " + parser.get('ftp', 'filename'),
                   open(cust_path + '/static/' + parser.get('ftp', 'filename'), 'r'))
    ftp.close()
    print "Uploaded ..."


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
    pickle.dump(known_stories, open(cust_path + "/technowatch.data", "wb"))
    if parser.get('wsgi', 'activated') == "True":
        fg.rss_file(cust_path + '/static/rss.xml')
    if parser.get('ftp', 'activated') == "True":
        upload()

# Initialize global variable
try:
    known_stories = pickle.load(open(cust_path + "/technowatch.data", "rb"))
except IOError:
    known_stories = {}
build()


def check_dribble():
    rebuild = False
    # requesting dribble
    html_doc = requests.get('https://dribbble.com/shots?list=animated').content
    soup = BeautifulSoup(html_doc)
    for li in soup.find_all('li', {'class': 'group'}):
        try:
            if li.get('id') is not None:
                key = "drib-" + li.get('id')
                if key not in known_stories:
                    link = "https://dribbble.com" + li.find("a", {'class': 'dribbble-link'}).get('href')
                    img = li.find("noscript").find("img").get('src').replace('_teaser', '')
                    item = {'title': li.find('strong').get_text(),
                            'url': link,
                            'by': li.find("a", {"class": 'url'}).get('title'),
                            'crawledDate': datetime.datetime.now().replace(tzinfo=pytz.utc),
                            'type': "dribble",
                            'key': key,
                            'desc': "li.find('strong').get_text()<br />"
                                    "<a href='" + link + "'>"
                                    "<img src='" + img + "' />"
                                    "</a>"}
                    known_stories[key] = item
                    rebuild = True
        except:
            print "Dribble bugged..."
    return rebuild


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
        try:
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
        except:
            print "Product Hunt bugged..."
    return rebuild


def check_hackernews():
    rebuild = False
    # API request for top stories
    noise = int(parser.get('technowatch', 'hackernews_noise'))
    top = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json').json()[:noise]
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
    for check in (check_hackernews, check_githubtrend, check_producthunt):
        rebuild = True if check() else rebuild
    if rebuild:
        # If new stories, rebuilding feed
        build()


def clean():
    left = len(known_stories) - int(parser.get('technowatch', 'cache_min'))
    for item in sorted(known_stories.values(), key=operator.itemgetter('crawledDate')):
        del known_stories[item['key']]
        left -= 1
        if left == 0:
            return


def threaded():
    while True:
        check_news()
        time.sleep(int(parser.get('technowatch', 'refresh')))


if parser.get('wsgi', 'activated') == "True":
    @app.route('/')
    def show_rss():
        # Simply return cached RSS
        return app.send_static_file('rss.xml')


if __name__ == '__main__':
    thread = threading.Thread(None, threaded, None)
    thread.start()
    if parser.get('wsgi', 'activated') == "True":
        app.run(host=parser.get('wsgi', 'host'), port=int(parser.get('wsgi', 'port')))
