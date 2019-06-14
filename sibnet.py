#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import math
import string
import urllib.request
import mechanize
import pandas as pd
import re

from functools import lru_cache
from urllib.parse import urlencode, urlparse, urlunparse, quote_plus
from bs4 import BeautifulSoup
from fuzzysearch import find_near_matches
from parsers import ongoings
from parsers import parser, misc, tools
DATE_FORMAT = parser.DATE_FORMAT

class SearchPattern:
	def __init__(self, search_pattern, get_authors, get_team, get_language, get_quality, get_kind):
		self.search_pattern = re.compile(search_pattern)
		self.get_authors = get_authors
		self.get_team = get_team
		self.get_language = get_language
		self.get_quality = get_quality
		self.get_kind = get_kind

	def search(self, s):
		return self.search_pattern.search(s)

class SearchResult:
	def __init__(self, searchPatterns, text):
		found = False
		self.searchPattern = None
		for searchPattern in searchPatterns:
			match = searchPattern.search(text)
			if match:
				self.searchPattern = searchPattern
				break

		self.text = text
	
	def _get_authors(self):
		if not self.searchPattern:
			return None

		match_group = self.searchPattern.search(self.text).group()
		return self.searchPattern.get_authors(match_group)

	def get_team(self):
		if not self.searchPattern:
			return None

		match_group = self.searchPattern.search(self.text).group()
		return self.searchPattern.get_team(match_group)

	def get_authors(self):
		authors = self._get_authors()
		team = self.get_team()

		if not authors or not team:
			return ""

		return "{team} ({authors})".format(team = team, authors = " & ".join(authors)[:-1])

	def get_quality(self):
		if not self.searchPattern:
			return None

		return self.searchPattern.get_quality(self.text)

	def get_kind(self):
		if not self.searchPattern:
			return None

		return self.searchPattern.get_kind(self.text)

	def get_language(self):
		if not self.searchPattern:
			return None

		return self.searchPattern.get_language(self.text)

class SibnetParser(parser.Parser):
	headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.1144'}

	to_shiki_kind = {"озвучка": "fandub", "subtitles": "subtitles", "субтитры": "subtitles"}

	episode_tokens = ["серия", "episode"]

	anime_aliases = {}
	
	def get_video_id(self, url):
		return url.split("/video")[-1].split("-")[0]

	def url_to_embed(self, url):
		return self.build_url(netloc = self.netloc,
				path = "/shell.php?videoid=%s" % self.get_video_id(url))

	def __init__(self, query_parameter = "text", fetch_latest_episode = True):
		self.scheme = "https"
		self.netloc = "video.sibnet.ru"
		self.fetch_latest_episode = fetch_latest_episode
		path = "/search.php"
		url = urllib.parse.urlunparse((self.scheme, self.netloc, path, None, None, None))
		main_url = urllib.parse.urlunparse((self.scheme, self.netloc, "", None, None, None))
		self.query_kwargs = {
				"rubid": "0",
				"duration": "0",
				"inname": "1",
				"intext": "0",
				"inkeyw": "0",
				"inalbom": "0",
				"sortby": "0",
				"panel": "open",
				query_parameter: "%s",
				"userlogin": ""
		}

		self.search_patterns = [SearchPattern(
			"\[Озвучка: [\wWdDsS].*\([\wWdDsS].*\)\]",
			get_authors = lambda s: s.split(": ")[-1].split("(")[0].split(", "),
			get_team = lambda s: s.split("(")[-1].split(")")[0],	
			get_language = lambda s: "russian",
			get_kind = lambda s: self.to_db_kind["fandub"],
			get_quality = lambda s: "unknown"
		)]

		super().__init__(url = url, main_url = main_url, headers = self.headers, query_kwargs = self.query_kwargs, query_parameter = query_parameter)
		self.setup_urlopener()

	def search_anime(self, anime_english, type_ = ""):
		names = [anime_english]

		if anime_english in misc.ALIASES:
			names += misc.ALIASES[anime_english]

		built_url = self.build_search_url(anime_english)

		found = False
		for anime_name in names:
			page_name = "%s.html" % anime_name
			page_data = self.load_page(page_name)
			print(anime_name)
			print(names)
			if not page_data:
				try:
					res = self.browser_open(built_url)
				except RuntimeError:
					tools.catch()
					return self.handler_resource_is_unavailable()
				page_data = res.get_data()
				redir_url = res.geturl()

			# not found
			html = BeautifulSoup(page_data, features = "html5lib")
			p = html.find("div", {"class": "content"}).find("p", {"style": "margin-top:20px; text-align:center;"})
			if p and p.text == "По Вашему запросу ничего не найдено":
				print("not found")
				continue

			if not page_data:
				print("not page_data")
				continue
			self.save_page(page_name, page_data)
			found = True
			self.anime_aliases[anime_english] = anime_name
			break

		if not found:
			return None

		return page_data

	def validate_results_page(self, anime_page):
		search_tit = [s for s in anime_page.find("div", {"class": "search_tit"}).strings]
		if (len(search_tit) != 2) or (search_tit[0] != "Найдено видеороликов: ") or (not search_tit[1].isdigit()):
			return None

		results_len = int(search_tit[1])
		return results_len

	def get_episode_num(self, search_result):
		tokens = [t for t in search_result.split(" ") if t]

		episode_token_idx = -1
		episode_token_name = ""
		for token in self.episode_tokens:
			if token in tokens:
				episode_token_idx = tokens.index(token)
				episode_token_name = token
				break

		if episode_token_idx < 0:
			return None

		episode_num = None
		try:
			#print("idx = %d (%s), tokens: %s" % (episode_token_idx, tokens[episode_token_idx], str(tokens)))
			if tokens[episode_token_idx - 1].isdigit():
				episode_num = int(tokens[episode_token_idx - 1])

			if tokens[episode_token_idx + 1].isdigit():
				episode_num = int(tokens[episode_token_idx + 1])

		except IndexError:
			tools.catch()
			pass


		return episode_num

	def parse_results_page(self, anime_page):
		try:
			entries = anime_page.find("table", {"class": "video_lst_v"}).find_all("table", {"class": "video_cell"})
		except:
			tools.catch()
			return {}

		results = {}

		for e in entries:
			try:
				url = e.find("div", {"class": "search_name"}).find("a")
				episode_num = self.get_episode_num(url.text)

				print(url.text)
				if not episode_num:
					continue

				if not episode_num in results:
					results[episode_num] = []

				results[episode_num].append((url.find("span").get("title"), url.get("href")))
			except:
				tools.catch()
				continue

		return results

	def merge_results(self, res1, res2):
		for (k, v) in res2.items():
			if not k in res1:
				res1[k] = []
			
			res1[k] += res2[k]

		return res1

	@lru_cache(maxsize = None)
	def get_parsed_results(self, anime_english, pages_total):
		query_kwargs = self.query_kwargs.copy()
		videos = {}
		for page_idx in range(1, pages_total + 1):
			print("processing page (%d of %d)" % (page_idx, pages_total))
			query_kwargs["page"] = str(page_idx)
			next_page_url = self.build_search_url(self.anime_aliases[anime_english], query_kwargs = query_kwargs)
			page_name = os.path.join(anime_english, "%d.html" % page_idx)
			anime_page = BeautifulSoup(self.load_or_save_page(page_name, next_page_url), features = "html5lib")

			results = self.parse_results_page(anime_page)
			print(results)
			videos = self.merge_results(videos, results)

		return videos

	@lru_cache(maxsize = None)
	def get_videos_list(self, anime_english, episode_num, type_ = ""):
		anime_page = BeautifulSoup(self.search_anime(anime_english, type_), features = "html5lib")
		if not anime_page:
			return self.handler_epidode_not_found(anime_english, episode_num)

		results_len = self.validate_results_page(anime_page)

		if (not results_len):
			print(results_len)
			return self.handler_epidode_not_found(anime_english, episode_num)

		pages_total = math.ceil(results_len / 30)
		query_kwargs = self.query_kwargs.copy()
		videos = self.get_parsed_results(anime_english, pages_total)

		if not episode_num in videos:
			print(videos)
			return self.handler_epidode_not_found(anime_english, episode_num)

		videos_list = pd.DataFrame(columns = ["url", "episode", "kind", "quality", "video_hosting", "language", "author"])

		for text, url in videos[episode_num]:
			searchResult = SearchResult(self.search_patterns, text)
			authors = searchResult.get_authors()
			quality = searchResult.get_quality() or "unknown"
			language = searchResult.get_language()
			kind = searchResult.get_kind()

			if not (language or kind or authors):
				continue

			videos_list = videos_list.append({
				"url": self.url_to_embed(url),
				"episode": str(episode_num),
				"video_hosting": self.netloc,
				"author": authors,
				"quality": quality,
				"language": language,
				"kind": kind
			}, ignore_index = True)

		return videos_list
