# Parsers for PlayShikiApp
## Overview
This repository is aiming to provide an automated import of anime videos for [PlayShikiServer](https://github.com/PlayShikimoriApp/PlayShikiServer) or a compatible backend server. Everything below assumes you are already familiar with some basic REST stuff and running such server.

## How exactly it's supposed to work
This repository tracks [shikimori](shikimori.one) ongoings and tries to find anime videos on other related resources.

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
from parsers import playshikiapp
playshikiapp.save(format = "sql")
```

This can take a while before all ongoings are fetched.
At finish, this script will produce "ongoings.sql" file in the current repository. Another supported format is pkl (a raw dump of Python object to a file).

### Supported external sites
For now this script only supports fetching episodes from smotret-anime-365.ru . It shouldn't be hard to add some other sites like sovetromantica.com . Some work on this already done by [AltWatcher extension](https://openuserjs.org/scripts/Lolec/Alt_Watcher_v3) (which makes a GET request to the internal sites' search engines).
