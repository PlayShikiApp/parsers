#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import string
import urllib.request
import mechanize
import pandas as pd
import demjson

from copy import deepcopy
from percache import Cache
from urllib.parse import urlencode, urlparse, urlunparse, quote_plus
from bs4 import BeautifulSoup
from shikimori.routes import shiki_db_df
from shikimori import app
from parsers import ongoings
from parsers import parser, misc, tools
from parsers.parser import MEDIA_KIND_VIDEOS, MEDIA_KIND_TORRENTS
DATE_FORMAT = parser.DATE_FORMAT

class KodikParser(parser.Parser):
	headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.1144'}
	supported_media_kinds = [MEDIA_KIND_VIDEOS]
	
	to_shiki_kind = {"voice": "fandub", "subtitles": "subtitles"}
	def __init__(self, query_parameter = "shikimoriID", fetch_latest_episode = True):
		self.scheme = "http"
		self.netloc = "kodikapi.com"
		self.fetch_latest_episode = fetch_latest_episode
		path = "get-player"
		url = urllib.parse.urlunparse((self.scheme, self.netloc, path, None, None, None))
		main_url = urllib.parse.urlunparse((self.scheme, self.netloc, "", None, None, None))
		query_kwargs = {"token": "447d179e875efe44217f20d1ee2146be", query_parameter: "%d"}
		super().__init__(url = url, main_url = main_url, query_kwargs = query_kwargs, query_parameter = query_parameter)
		self.setup_urlopener()
		
	def search_anime(self, anime_english, anime_aliases = [], type_ = "", anime_id = -1):
		if anime_id < 0:
			raise RuntimeError("anime_id must be provided")

		names = [anime_english]

		found = False
		for anime_name in names:
			page_name = "%s.html" % anime_name
			page_data = self.load_page(page_name)
			if not page_data:
				try:
					query_kwargs = deepcopy(self.query_kwargs)
					query_kwargs[self.query_parameter] %= anime_id

					built_url = self.build_search_url(query_kwargs = query_kwargs)
					res = self.browser_open(built_url)
					json_resp = demjson.decode(res.get_data().decode("u8"))
					try:
						page_url = "https:" + json_resp["link"]
						res = self.browser_open(page_url)
						page_data = res.get_data()
					except:
						return self.handler_resource_is_unavailable()
				except RuntimeError:
					return self.handler_resource_is_unavailable()

				if not page_data:
					continue
			self.save_page(page_name, page_data)
			found = True
			break

		if not found:
			return None

		return page_data

	#@Cache(prefix="KodikParser")
	def get_videos_list(self, anime_english, episode_num, type_ = "", anime_id = -1):
		if anime_id < 0:
			raise RuntimeError("anime_id must be provided")

		anime_page = self.search_anime(anime_english, type_, anime_id = anime_id)
		if not anime_page:
			return self.handler_anime_not_found(anime_english)

		try:
			content_main = BeautifulSoup(anime_page, features = "html5lib")
			options = content_main.find("div", {'class': 'serial-series-box'}).find_all("option")
		except:
			return self.handler_epidode_not_found(anime_english, episode_num)

		videos_list = pd.DataFrame(columns = ["url", "episode", "kind", "quality", "video_hosting", "language", "author"])
		for o in options:
			quality = "720p"
			episode_num_ = o.get("value")
			if episode_num != int(episode_num_):
				continue

			data_id = o.get("data-id")
			data_hash = o.get("data-hash")
			tmp_url = "https://aniqit.com/seria/" + data_id + "/" + data_hash + "/720p"
			page_name = "%s-%s.html" % (anime_english, episode_num_)
			page_data = self.load_page(page_name)
			if not page_data:
				try:
					res = self.browser_open(tmp_url)
					page_data = res.get_data()
				except RuntimeError:
					return self.handler_epidode_not_found(anime_english, episode_num)

				if not page_data:
					continue
			self.save_page(page_name, page_data)
			content = BeautifulSoup(page_data, features = "html5lib")
			options = content.find("div", {'class': 'movie-translations-box'}).find_all("option")

			for op in options:
				url = "https://aniqit.com/seria/" + op.get("data-media-id") + "/" + op.get("data-media-hash") + "/720p"
				shiki_kind = self.to_shiki_kind[op.get("data-translation-type")]
				author = op.text

				videos_list = videos_list.append({
					"url": url,
					"episode": str(episode_num_),
					"video_hosting": "aniqit",
					"author": author,
					"quality": quality,
					"language": "russian",
					"kind": self.to_db_kind[shiki_kind]
				}, ignore_index = True)
		return videos_list
