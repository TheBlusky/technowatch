# technowatch
Yet another RSS technological watch.

## Features
An example worth a thousand words, so here is an example: http://bit.ly/1IPwyoH (read it as an RSS feed if your browser shows some noise ...(ex: http://bit.ly/1FsTMgo))

Ok... It wasn't as self explanatory as expected... This is an RSS feed that contains :
  - TOP 10 elements of hackernews (https://news.ycombinator.com/)
  - TOP 10 elements of producthunt (http://www.producthunt.com/)
  - Trending github repositories (https://github.com/trending)
  
The script scrap those site every minute, and if something is new, it create a new item inside the RSS feed. As simple as that.
If you use a RSS agregator, it's a good way to be up-to-date of popular itmes (rather than "new" items").
## Install
```bash
git clone https://github.com/TheBlusky/technowatch.git
cd technowatch
vim technowatch.conf
```
## Use it
```bash
python technowatch.py
```
## Configuration
```bash
vim technowatch.conf
```
```
[technowatch]
cache_max: Maximum items in memory (default: 100)
cache_min: Items to keep once cache exceed "cache_max" (default: 50)
refresh: Time in seconds between refreshing news (default: 60)
name: Name of the RSS file (default: Technowatch)
link: Link of the RSS file (default: http://dan.lousqui.fr)
hackernews_noise: Top file to listen on hackernews (default: 10)
[wsgi]
activated: If WSGI interface is activated (default True)
host: Listening interface (default: 0.0.0.0)
port: Listening port (default: 5060)
[ftp]
activated: If FTP upload is activated (default False)
host= FTP Hostname
user: FTP User
pass: FTP Password
path: FTP Path
filename: Filename to upload
```
## Requirement
```
beautifulsoup4>=4.3.2
configparser>=3.3.0r2
feedgen>=0.3.1
flask>=0.10.1
requests>=2.2.1
```
## Extension
If you want to monitor another website, create a new method that respect the follwoing rules:
```python
def check_XXX():
    rebuild = False
    # Here some code to request the website
    XXX
    for item in some_loop():
        # Here some code for some parsing
        XXX
        if index not in known_stories:
            # Create an item object that have the following keys
            item = {'title': YYY,
                    'url': YYY,
                    'by': YYY,
                    'crawledDate': datetime.datetime.now().replace(tzinfo=pytz.utc),
                    'type': XXX,
                    'key': XXX,
                    'desc': XXX}
            # Add the item to know_stories
            known_stories[title] = item
            # Tell the system to update the RSS
            rebuild = True
    return rebuild
```
and add the following in `check_news`
```python
rebuild = True if check_XXX() else rebuild
```