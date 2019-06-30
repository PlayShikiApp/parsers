#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import string
import urllib.request
import mechanize
import pandas as pd
import demjson

from percache import Cache
from urllib.parse import urlencode, urlparse, urlunparse, quote_plus
from bs4 import BeautifulSoup
from fuzzysearch import find_near_matches
from parsers import ongoings
from parsers import parser, misc, tools
DATE_FORMAT = parser.DATE_FORMAT

class AnilibriaParser(parser.Parser):
	headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.1144'}

	url_to_embed = lambda self, url: self.build_url(path = url.replace("]//", "]https://"))
	get_quality = lambda self, url: ("%dp" % max([int(i.split("[")[-1].split("]")[0][:-1]) for i in url.split(",")]))

	def __init__(self, query_parameter = "search", fetch_latest_episode = True):
		self.scheme = "https"
		self.netloc = "www.anilibria.tv"
		self.fetch_latest_episode = fetch_latest_episode
		path = "/public/search.php"
		url = urllib.parse.urlunparse((self.scheme, self.netloc, path, None, None, None))
		main_url = urllib.parse.urlunparse((self.scheme, self.netloc, "", None, None, None))
		query_kwargs = {query_parameter: "%s"}

		super().__init__(url = url, main_url = main_url, headers = self.headers, query_kwargs = query_kwargs, query_parameter = query_parameter)
		self.setup_urlopener()

	def search_anime(self, anime_english, anime_aliases = [], type_ = ""):
		names = [anime_english]

		if anime_english in misc.ALIASES:
			names += misc.ALIASES[anime_english]

		found = False
		for anime_name in names:
			page_name = "%s.html" % anime_name
			page_data = self.load_page(page_name)
			#print(anime_name)
			if not page_data:
				#print("!page_data")
				try:
					built_url, query_kwargs = self.build_search_url(anime_name, method = "POST")
					res = self.browser_open(built_url, method = "POST", data = query_kwargs)
				except RuntimeError:
					tools.catch()
					continue
				resp = res.read()

				if not resp:
					self.save_page(page_name, b"")
					#print("!resp")
					continue

				try:
					resp = demjson.decode(resp)
				except:
					tools.catch()
					continue

				if not "err" in resp or not "mes" in resp or resp["err"] != "ok":
					print("resp is not ok")
					continue

				resp_data = resp["mes"]
				if not resp_data:
					print("!resp_data")
					continue

				resp_data = BeautifulSoup(resp_data, features = "html5lib")
				anime_page_url = resp_data.find("a")
				if not anime_page_url:
					print("!anime_page_url")
					continue

				anime_page_url = anime_page_url.get("href")
				try:
					res = self.browser_open(self.build_url(path = anime_page_url))
				except RuntimeError:
					tools.catch()
					continue

				page_data = res.get_data()
					
				
			self.save_page(page_name, page_data)
			found = True
			break

		if not found:
			return None

		return page_data

	@Cache(prefix="AnilibriaParser")
	def parse_anime_page(self, anime_english, type_ = ""):
		anime_page = self.search_anime(anime_english, type_)
		if not anime_page:
			return self.handler_anime_not_found(anime_english)

		content_main = BeautifulSoup(anime_page, features = "html5lib")
		
		authors = "[Anilibria]"
		release_info = content_main.find("div", {"id": "xreleaseInfo"})
		if release_info:
			release_info = list(release_info.strings)
			if 'Озвучка:' in release_info:
				try:
					dubbers = release_info[release_info.index('Озвучка:') + 1].lstrip()
					dubbers = " & ".join(dubbers.split(", "))
					authors += "(%s)" % dubbers

				except IndexError:
					tools.catch()
		

		videos = {}
		videos_start_idx = anime_page.find(b"new Playerjs(")
		if videos_start_idx < 0:
			return authors, videos

		videos_end_idx = anime_page.find(b"});", videos_start_idx)

		if videos_end_idx < 0:
			return authors, videos

		videos_unparsed = anime_page[videos_start_idx + len(b"new Playerjs("): videos_end_idx + 1]

		try:
			videos = {int(f["id"].split("s")[-1]): f["file"] for f in demjson.decode(videos_unparsed)["file"]}
		except:
			tools.catch()
		
		return authors, videos
					

	@Cache(prefix="AnilibriaParser")
	def get_videos_list(self, anime_english, episode_num, type_ = ""):
		authors, videos = self.parse_anime_page(anime_english, type_)

		if not episode_num in videos:
			return self.handler_epidode_not_found(anime_english, episode_num)
			
		if not authors:
			return self.handler_authors_not_found(anime_english)

		videos_list = pd.DataFrame(columns = ["url", "episode", "kind", "quality", "video_hosting", "language", "author"])

		video_url = videos[episode_num]
		quality = "unknown"
		try:
			quality = self.get_quality(video_url)
		except:
			tools.catch()

		videos_list = videos_list.append({
			"url": self.url_to_embed(video_url),
			"episode": str(episode_num),
			"video_hosting": self.netloc,
			"author": authors,
			"quality": quality,
			"language": "russian",
			"kind": self.to_db_kind["fandub"]
		}, ignore_index = True)

		return videos_list
