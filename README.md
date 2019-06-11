# Parsers for PlayShikiApp
## Overview
This repository is aiming to provide an automated import of anime videos for [PlayShikiServer](https://github.com/PlayShikimoriApp/PlayShikiServer) or a compatible backend server. Everything below assumes you are already familiar with some basic REST stuff and running such server.

## How exactly it's supposed to work
This repository tracks [shikimori](https://shikimori.one) ongoings and tries to find anime videos on other related resources.

## Quick start
#### Clone this repo
This repo is configured as a submodule of PlayShikiServer:
```
cd PlayShikiServer
git clone https://github.com/PlayShikimoriApp/parsers
```
#### Install the dependencies:
```
cd parsers
pip3 install -r requirements.txt
cd ..
```

For now parsers use a hardcoded page (TODO: fix this) containing ongoings:
```
cp ongoings_07.06.2019.html ..
```

Above is the sample page for this guide.
It should be manually updated each day or each chosen period of time to track new ongoings.

#### Start webscraping the stuff
In order not to hurt anyone, this repo tries to minimize amount of requests to the external anime-related sites by caching the scraped stuff. Cache is invalidated each day, but previously saved pages aren't removed automatically, so it can quickly grow in a size.

From python3 interpreter shell run (assuming you're in a toplevel directory, e.g. PlayShikiServer):
```
>>> from parsers import playshikiapp
>>> playshikiapp.save(format = "sql")
```

This can take a while before all ongoings are fetched.
At finish, this script will produce "ongoings.sql" file in the current directory. Another supported format is pkl (a raw dump of Python object to a file).

#### Retrieve some info about an ongoing:
```
>>> from parsers import ongoings
>>> ongoings.main()

>>> ongoings.ONGOING_IDS[0]
38524
>>> ongoings.get_ongoing_info(38524)
{'Тип:': 'TV Сериал', 'Эпизоды:': '7 / 10', 'Следующий эпизод:': '16 июня 18:10', 'Длительность эпизода:': ['23 мин.'], 'Статус:': ['\xa0с 29 апр. 2019 г.'], 'Жанры:': ['Action', 'Military', 'Mystery', 'Super Power', 'Drama', 'Fantasy', 'Shounen'], 'Рейтинг:': ['R-17'], 'Альтернативные названия:': ['···'], 'episodes_available': 7, 'episodes_total': 10, 'next_episode': '16.06.2019', 'type': 'tv', 'date_created': '29.04.2019', 'anime_english': 'Shingeki no Kyojin Season 3 Part 2', 'anime_russian': 'Вторжение гигантов 3. Вторая часть'}
```

### Supported external sites
For now this script only supports fetching episodes from smotret-anime-365.ru . It shouldn't be hard to add some other sites like sovetromantica.com . Some work on this already done by [AltWatcher](https://openuserjs.org/scripts/Lolec/Alt_Watcher_v3) extension (which makes a GET request to the internal sites' search engines).
