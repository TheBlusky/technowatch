from bs4 import BeautifulSoup
import datetime
import pytz
import requests

__author__ = 'Blusky'


def check_dribble():
    rebuild = False
    # requesting dribble
    html_doc = requests.get('https://dribbble.com/shots?list=animated').content
    soup = BeautifulSoup(html_doc)
    for li in soup.find_all('li', {'class': 'group'}):
        try:
            if li.get('id') != None:
                key = "drib-" + li.get('id')
                if key not in known_stories:
                    link = "https://dribbble.com" + li.find("a",{'class': 'dribbble-link'}).get('href')
                    img = li.find("noscript").find("img").get('src').replace('_teaser','')
                    item = {'title': li.find('strong').get_text(),
                            'url': link,
                            'by': li.find("a",{"class":'url'}).get('title'),
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

known_stories = {}
check_dribble()
for a in known_stories:
    print known_stories[a]