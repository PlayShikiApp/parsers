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
from parsers import parser, misc, tools
from parsers.parser import MEDIA_KIND_VIDEOS, MEDIA_KIND_TORRENTS
DATE_FORMAT = parser.DATE_FORMAT

from shiki2sovetromantica import shiki2sovetromantica

class SRParser2(parser.Parser):
	headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.1144'}

	to_shiki_kind = {"dubbed": "fandub", "subtitles": "subtitles"}

	get_episode_num = lambda self, url: url.split("/")[-1].split("_")[-1].split("-")[0]
	get_anime_id = lambda self, url: url.split("/")[-2].split("-")[0]
	get_anime_kind = lambda self, url: url.split("/")[-1].split("_")[-1].split("-")[-1]

	supported_media_kinds = [MEDIA_KIND_VIDEOS]

	def url_to_embed(self, url, kind):
		return self.build_url(netloc = self.netloc,
				path = "embed/episode_%s_%s-%s" % (self.get_anime_id(url), self.get_episode_num(url), kind))

	def __init__(self, query_parameter = "query", fetch_latest_episode = True):
		self.scheme = "https"
		self.netloc = "sovetromantica.com"
		self.fetch_latest_episode = fetch_latest_episode
		path = "/anime"
		url = urllib.parse.urlunparse((self.scheme, self.netloc, path, None, None, None))
		main_url = urllib.parse.urlunparse((self.scheme, self.netloc, "", None, None, None))
		query_kwargs = {query_parameter: "%s"}

		super().__init__(url = url, main_url = main_url, headers = self.headers, query_kwargs = query_kwargs, query_parameter = query_parameter)
		self.setup_urlopener()

	def search_anime(self, anime_english, anime_aliases = [], type_ = "", anime_id = -1):
		if anime_id < 0:
				raise RuntimeError("anime_id must be provided")
		if not anime_id in shiki2sovetromantica:
			return None

		page_url = shiki2sovetromantica[anime_id]
		page_name = "%d.html" % anime_id
		page_data = self.load_page(page_name)
		if not page_data:
			try:
				res = self.browser_open(page_url)
				page_data = res.get_data()
			except:
				return self.handler_resource_is_unavailable()
		self.save_page(page_name, page_data)
		return page_data

	#@Cache(prefix="SRParser2")
	def get_videos_list(self, anime_english, episode_num, type_ = "", anime_id = -1):
		if anime_id < 0:
				raise RuntimeError("anime_id must be provided")
		episodes = []
		anime_page = self.search_anime(anime_english, type_, anime_id = anime_id)
		if not anime_page:
			return self.handler_anime_not_found(anime_english)


		content_main = BeautifulSoup(anime_page, features = "html5lib")
		try:
			episodes += [a.get("href") for a in content_main.find("div", {"class": "episodes-slick"}).find_all("a")]
		except AttributeError:
			pass
		#print(episodes)
		#return self.handler_episodes_list_not_found(anime_english)

		if not episodes:
			return self.handler_episodes_list_not_found(anime_english)

		nav = {}
		try:
			nav = {a.text: a.get("href") for a in content_main.find("div", {"class": "episode_info"}).find("nav").find_all("a") }
		except:
			tools.catch()

		if "Озвучка" in nav:
			url = self.build_url(path = nav["Озвучка"])
			page_name = os.path.join(anime_english, "fandub.html")
			#print(page_name, url)
			anime_page = self.load_or_save_page(page_name, url)
			content = BeautifulSoup(anime_page, features = "html5lib")
			try:
				episodes += [a.get("href") for a in content.find("div", {"class": "episodes-slick"}).find_all("a")]
				#print(episodes)
			except AttributeError:
				pass

		videos_list = pd.DataFrame(columns = ["url", "episode", "kind", "quality", "video_hosting", "language", "author"])
		quality = "unknown"
		author = "sovetromantica"

		for url in episodes:
			episode_num_ = self.get_episode_num(url)
			if not episode_num_ or not (episode_num_.isdigit()):
				continue

			episode_num_ = int(episode_num_)

			if episode_num_ != episode_num:
				continue

			kind = self.get_anime_kind(url)
			shiki_kind = self.to_shiki_kind[kind]
			all_authors = content.find_all("div", {"class": "anime-team"})
			if shiki_kind == "subtitles":
				try:
					author = " & ".join([s for s in all_authors[0].strings if not s.isspace()])
					#print(author)
				except:
					pass
				try:
					all_authors = [[i for i in list(d.strings) if not i.isspace()] for d in content_main.find_all("div", {"class": "anime-team"})][0]
					#author = " & ".join(all_authors)
					#print(author)
				except:
					pass

			try:
				if shiki_kind == "fandub":
					author = " & ".join([s for s in all_authors[1].strings if not s.isspace()])
					#print(author)
			except (IndexError, AttributeError):
				tools.catch()
				continue

			#print(url, kind)
			videos_list = videos_list.append({
				"url": self.url_to_embed(url, kind),
				"episode": str(episode_num_),
				"video_hosting": self.netloc,
				"author": author,
				"quality": quality,
				"language": "russian",
				"kind": self.to_db_kind[shiki_kind]
			}, ignore_index = True)

		return videos_list
