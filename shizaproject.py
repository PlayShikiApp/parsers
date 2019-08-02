#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import string
import urllib.request
import mechanize
import pandas as pd

from percache import Cache
from urllib.parse import urlencode, urlparse, urlunparse, quote_plus
from bs4 import BeautifulSoup
from fuzzysearch import find_near_matches
from fuzzywuzzy import fuzz
from parsers import ongoings
from parsers import parser, misc, tools
from parsers.parser import MEDIA_KIND_VIDEOS, MEDIA_KIND_TORRENTS
DATE_FORMAT = parser.DATE_FORMAT

class ShizaParser(parser.Parser):
	headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.1144'}

	supported_media_kinds = [MEDIA_KIND_TORRENTS]

	def __init__(self, query_parameter = "q", fetch_latest_episode = True):
		self.scheme = "http"
		self.netloc = "shiza-project.com"
		self.fetch_latest_episode = fetch_latest_episode
		path = "/releases/search"
		url = urllib.parse.urlunparse((self.scheme, self.netloc, path, None, None, None))
		main_url = urllib.parse.urlunparse((self.scheme, self.netloc, "", None, None, None))
		query_kwargs = {query_parameter: "%s"}

		super().__init__(url = url, main_url = main_url, headers = self.headers, query_kwargs = query_kwargs, query_parameter = query_parameter)
		self.setup_urlopener()

	def _find_best_match(self, resp, anime_names):
		page = BeautifulSoup(resp, features = "html5lib")
		urls = [article.find("a") for article in page.find_all("article")]
		if not urls:
			return
		
		try:
			results = {a.get("title").split(",")[0]: a.get("href") for a in urls for a in urls}
		except Exception as e:
			tools.catch(str(e.reason))
			return

		print(results)
		best_score = 0
		best_result = None
		print("_find_best_match: names: %s" % str(anime_names))

		for name in anime_names:
			print("_find_best_match: name: %s" % name)

			for k, v in results.items():
				score = fuzz.ratio(name, k)
				if score > best_score:
					best_score = score
					best_result = v
					print("%s: score=%d" % (best_result, best_score))

		if not best_result:
			return

		if best_score < self.name_match_threshold:
			print("%s has score %d, rejecting" % (str(best_result), best_score))
			best_result = None

		return best_result
	def search_anime(self, anime_english, anime_aliases = [], type_ = ""):
		names = [anime_english] + anime_aliases

		if anime_english in misc.ALIASES:
			names += misc.ALIASES[anime_english]

		found = False
		for anime_name in names:
			page_name = "%s.html" % anime_name
			page_data = self.load_page(page_name)
			print(anime_name)
			if not page_data:
				print("!page_data")
				try:
					built_url = self.build_search_url(anime_name)
					res = self.browser_open(built_url)
				except RuntimeError:
					tools.catch()
					continue
				resp = res.read()

				if not resp:
					print("!resp")
					continue

				anime_page_url = self._find_best_match(resp, anime_names = names)
				print("search: anime_page_url=%s" % anime_page_url)
				if not anime_page_url:
					print("!anime_page_url")
					continue
				try:
					#print(anime_page_url)
					res = self.browser_open(anime_page_url)
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