#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import string
import urllib.request
import mechanize
import pandas as pd

from functools import lru_cache
from urllib.parse import urlencode, urlparse, urlunparse, quote_plus
from bs4 import BeautifulSoup
from fuzzysearch import find_near_matches
from parsers import ongoings
from parsers import parser, misc
DATE_FORMAT = parser.DATE_FORMAT

class SRParser(parser.Parser):
	headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.1144'}

	get_episode_num = lambda self, url: url.split("/")[-1].split("_")[-1]
	get_anime_id = lambda self, url: url.split("_")[1]
	url_to_embed = lambda self, url: self.build_url(netloc = self.netloc, path = "embed/episode_%s_%s-subtitles" % (self.get_anime_id(url), self.get_episode_num(url)))

	def __init__(self, query_parameter = "query", fetch_latest_episode = False):
		self.scheme = "https"
		self.netloc = "sovetromantica.com"
		self.fetch_latest_episode = fetch_latest_episode
		path = "/anime"
		url = urllib.parse.urlunparse((self.scheme, self.netloc, path, None, None, None))
		main_url = urllib.parse.urlunparse((self.scheme, self.netloc, "", None, None, None))
		query_kwargs = {query_parameter: "%s"}

		super().__init__(url = url, main_url = main_url, headers = self.headers, query_kwargs = query_kwargs, query_parameter = query_parameter)
		self.setup_urlopener()

	def search_anime(self, anime_english, type_ = ""):
		built_url = self.build_search_url(anime_english)

		page_name = "%s.html" % anime_english
		page_data = self.load_page(page_name)
		if not page_data:
			try:
				res = self.browser_open(built_url)
			except RuntimeError:
				return self.handler_resource_is_unavailable()
			page_data = res.get_data()
			redir_url = res.geturl()

			if not page_data:
				return None
		self.save_page(page_name, page_data)
		return page_data

	@lru_cache(maxsize = None)
	def get_videos_list(self, anime_english, type_ = ""):
		anime_page = self.search_anime(anime_english, type_)
		if not anime_page:
			return self.handler_anime_not_found(anime_english)

		content = BeautifulSoup(anime_page, features = "html5lib")
		episodes = [a.get("href") for a in content.find_all("a", {"class": "episodeButtonDownload"})]

		if not episodes:
			return self.handler_episodes_list_not_found(anime_english)

		videos_list = pd.DataFrame(columns = ["url", "episode", "kind", "quality", "video_hosting", "language", "author"])
		anime_id = self.get_anime_id(episodes[0])
		if not anime_id.isdigit():
			return 
		anime_id = int(anime_id)
		quality = "unknown"
		author = "unknown"
		for url in episodes:
			episode_num = self.get_episode_num(url)
			if not episode_num or not (episode_num.isdigit()):
				continue

			episode_num = int(episode_num)
			try:
				author = " & ".join([s for s in b.find("div", {"class": "anime-team"}).strings if not s.isspace()])
			except:
				pass

			videos_list = videos_list.append({
				"url": self.url_to_embed(url),
				"episode": str(episode_num),
				"video_hosting": self.netloc,
				"author": author,
				"quality": quality,
				"language": "russian",
				"kind": self.to_db_kind["subtitles"]
			}, ignore_index = True)

		return videos_list

	
