# technowatch
Yet another RSS technological watch.

## Features

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
host: Listening interface (default: 0.0.0.0)
port: Listening port (default: 5060)
cache_max: Maximum items in memory (default: 100)
cache_min: Items to keep once cache exceed "cache_max" (default: 50)
refresh: Time in seconds between refreshing news (default: 60)
name: Name of the RSS file (default: Technowatch)
link: Link of the RSS file (default: http://dan.lousqui.fr)
hackernews_noise: Top file to listen on hackernews (default: 10)
## Requirement
beautifulsoup4>=4.3.2
configparser>=3.3.0r2
feedgen>=0.3.1
flask>=0.10.1
requests>=2.2.1
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