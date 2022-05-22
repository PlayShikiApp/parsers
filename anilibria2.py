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
from fuzzywuzzy import fuzz

from shikimori.models import AnimeVideo

from parsers import ongoings
from parsers import parser, misc, tools
from parsers.parser import MEDIA_KIND_VIDEOS, MEDIA_KIND_TORRENTS

from shiki2anilibria import shiki2anilibria
DATE_FORMAT = parser.DATE_FORMAT

class AnilibriaParser2(parser.Parser):
	headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.1144'}

	url_to_embed = lambda self, url: self.build_url(path = url.replace("]//", "]https://"))
	get_quality = lambda self, url: ("%dp" % max([int(i.split("[")[-1].split("]")[0][:-1]) for i in url.split(",")]))
	name_match_threshold = 93

	supported_media_kinds = [MEDIA_KIND_VIDEOS]

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

	def search_anime(self, anime_english, anime_aliases = [], type_ = "", anime_id = -1):
		if anime_id < 0:
				raise RuntimeError("anime_id must be provided")
		if not anime_id in shiki2anilibria:
			return None

		page_url = "https://www.anilibria.tv" + shiki2anilibria[anime_id]
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

	#@Cache(prefix="AnilibriaParser2")
	def parse_anime_page(self, anime_english, type_ = "", anime_id = -1):
		anime_page = self.search_anime(anime_english, anime_id = anime_id)
		if not anime_page:
			print("parse_anime_page: not found")
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


	#@Cache(prefix="AnilibriaParser2")
	def get_videos_list(self, anime_english, episode_num, type_ = "", anime_id = -1):
		if anime_id < 0:
				raise RuntimeError("anime_id must be provided")
		existing_video = AnimeVideo.query.filter(AnimeVideo.anime_english == anime_english, AnimeVideo.episode == episode_num, AnimeVideo.url.like("%libria%")).first()
		if existing_video:
			return self.handler_epidode_exists(anime_english, episode_num, existing_video.url)

		try:
			obj = self.parse_anime_page(anime_english, type_ = type_, anime_id = anime_id)
			authors, videos = obj
		except:
			#print("parse_anime_page returned %s" % str(obj))
			raise

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
