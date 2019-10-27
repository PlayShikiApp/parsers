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
from parsers import ongoings
from parsers import parser, misc
from parsers.parser import MEDIA_KIND_VIDEOS, MEDIA_KIND_TORRENTS

DATE_FORMAT = parser.DATE_FORMAT

class Anime365Parser(parser.Parser):
	headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.1144'}

	video_kinds = {
		"fandub": ["ozvuchka"],
		"subtitles": ["russkie-subtitry", "angliyskie-subtitry", "yaponskie-subtitry"],
		"raw": ["raw"]
	}

	language_by_kind = {
		"ozvuchka": "russian",
		"russkie-subtitry": "russian",
		"angliyskie-subtitry": "english",
		"yaponskie-subtitry": "japanese",
		"raw": "japanese"
	}

	supported_media_kinds = [MEDIA_KIND_VIDEOS]

	anime365_name_chars = string.ascii_letters + string.digits + " "

	def __init__(self, query_parameter = "q", fetch_latest_episode = True):
		self.scheme = "https"
		self.netloc = "smotret-anime.online"
		# for compatibility reasons
		self.netloc_alias = "smotretanime.ru"
		self.fetch_latest_episode = fetch_latest_episode
		path = "/catalog/search"
		url = urllib.parse.urlunparse((self.scheme, self.netloc, path, None, None, None))
		main_url = urllib.parse.urlunparse((self.scheme, self.netloc, "", None, None, None))
		query_kwargs = {query_parameter: "%s", "undefined": "", "dynpage": "1"}

		super().__init__(url = url, main_url = main_url, headers = self.headers, query_kwargs = query_kwargs, query_parameter = query_parameter)
		self.setup_urlopener()

	def to_hosting_anime_name(self, anime_english = "", url = ""):
		if anime_english:
			anime_english = anime_english.lower()
			return "".join([c for c in anime_english if c in self.anime365_name_chars]).replace(" ", "-")
		if url:
			return "-".join(url.split("/")[-1].split("-")[:-1])


	def search_anime(self, anime_english, anime_aliases = [], type_ = ""):
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

			# if not found
			if "search" in redir_url:
				results = BeautifulSoup(page_data, features = "html5lib").find_all("div", {"class": "m-catalog-item"})
				#print(len(results))
				if not results:
					return None

				found = False
				found_url = ""
				name = self.to_hosting_anime_name(anime_english = anime_english)
				names = [name]
				if anime_english in misc.ALIASES:
					for alias in misc.ALIASES[anime_english]:
						names.append(self.to_hosting_anime_name(anime_english = alias))

				for result in results:
					url = results[0].find("a").get("href")
					url_to_name = self.to_hosting_anime_name(url = url)
					#print(url_to_name, name)
					#print("check (%s == %s) or (%s == %s)" % (url_to_name, name, url_to_name, name + "-" + type_))
					for name in names:
						found = (url_to_name == name)					or \
							(url_to_name == name + "-" + type_)			or \
							(find_near_matches(url_to_name, name, max_l_dist=1))
						if found:
							break

					if found:
						found_url = url
						break

				if not found:
					return None
				try:
					res = self.browser_open(self.build_url(path = found_url))
				except RuntimeError:
					return self.handler_resource_is_unavailable()

			page_data = res.get_data()
			if not page_data:
				return None
		self.save_page(page_name, page_data)
		return page_data

	@Cache(prefix="Anime365Parser")
	def get_episodes_list(self, anime_english, type_ = ""):
		#print("[start] get_episodes_list: " + anime_english + ", " + type_)
		anime_page = self.search_anime(anime_english, type_)
		if not anime_page:
			return self.handler_anime_not_found(anime_english)

		content = BeautifulSoup(anime_page, features = "html5lib")
		episodes_list = content.find("div", {"class": "m-episode-list"})

		if not episodes_list:
			return self.handler_episodes_list_not_found(anime_english)

		episodes = [a.get("href") for a in episodes_list.find_all("a", {"class": "m-episode-item"})]
		res = dict()
		for e in episodes:
			url = self.build_url(path = e)
			episode_num = [part for part in e.split("/")[-1].split("-") if part.isdigit()]
			if not episode_num:
				continue

			episode_num = episode_num[0]
			if not episode_num.isdigit():
				continue
			episode_num = int(episode_num)

			res[episode_num] = url

		#print("[end] get_episodes_list")
		return res

	@Cache(prefix="Anime365Parser")
	def get_videos_list(self, anime_english, episode_num, type_ = ""):
		#print("[start] get_videos_list: " + anime_english + ", " + str(episode_num) + ", "+ type_)
		episodes_list = self.get_episodes_list(anime_english, type_)
		if (not episodes_list) or (not episode_num in episodes_list):
			return self.handler_epidode_not_found(anime_english, episode_num)

		anime_url = episodes_list[episode_num]
		page_name = os.path.join(anime_english, "%d.html" % episode_num)
		page_data = self.load_or_save_page(page_name, anime_url)

		content = BeautifulSoup(page_data, features = "html5lib")
		avalable_kinds = [i.get("href").split("/")[-1] for i in content.find("div", {"class": "m-select-translation-list"}).find_all("a")]

		kinds_dict = dict()
		for shiki_kind, kinds in self.video_kinds.items():
			kinds_dict[shiki_kind] = [kind for kind in kinds if kind in avalable_kinds]

		videos_list = pd.DataFrame(columns = ["url", "episode", "kind", "quality", "video_hosting", "language", "author"])
		url_to_embed = lambda url: self.build_url(netloc = self.netloc_alias, path = "translations/embed/" + url.split("-")[-1])
		for shiki_kind, kinds in kinds_dict.items():
			for kind in kinds:
				page_name = os.path.join(anime_english, str(episode_num), shiki_kind, "%s.html" % kind)
				page_data = self.load_or_save_page(page_name, os.path.join(anime_url, kind))

				b = BeautifulSoup(page_data, features = "html5lib")
				quality = "unknown"
				try:
					quality = max([int(a.text.split("(")[-1].split(")")[0][:-1]) for a in b.find("div", {"class": 'm-translation-view-download'}).find_all("a") if a.text.startswith("Скачать видео (")])
					quality = "%dp" % quality
				except AttributeError:
					pass

				content = BeautifulSoup(page_data, features = "html5lib")
				#print(videos_list)
				translations_list = content.find("div", {"class": "m-select-translation-list"})
				if not translations_list:
					continue

				for a in translations_list.find_all("a", {"class": "truncate"}):
					videos_list = videos_list.append({"url": url_to_embed(a.get("href")),
							    "episode": str(episode_num),
							    "video_hosting": self.netloc_alias,
							    "author": a.text,
							    "quality": quality,
							    "language": self.language_by_kind[kind],
							    "kind": self.to_db_kind[shiki_kind]
							   }, ignore_index = True)
		#print("[end] get_videos_list")
		return videos_list
