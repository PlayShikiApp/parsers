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
from shikimori.routes import shiki_db_df
from shikimori import app
from parsers import ongoings
from parsers import parser, misc, tools
from parsers.shiki2neko import shiki2neko
from parsers.neko2shiki import neko2shiki
from parsers.parser import MEDIA_KIND_VIDEOS, MEDIA_KIND_TORRENTS
DATE_FORMAT = parser.DATE_FORMAT



class NekoParser(parser.Parser):
	headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.1144'}
	languages = ['Неизвестный', 'Японский', 'Английский', 'Русский', 'Немецкий', 'Украинский', 'Китайский', 'Ромадзи']
	sources = ['Все', 'Оригинал', 'BlueRay']
	kinds = ['None', 'raw', 'subtitles', 'fandub']
	statuses = ['None', 'Удаленный', 'Сомнительный', 'Trustish', 'Проверенный', 'Модерированый', 'Абсолютный']
	supported_media_kinds = [MEDIA_KIND_VIDEOS]

	def __init__(self, query_parameter = "artId", fetch_latest_episode = True):
		self.scheme = "https"
		self.netloc = "api.nekomori.ch"
		self.fetch_latest_episode = fetch_latest_episode
		path = "players"
		url = urllib.parse.urlunparse((self.scheme, self.netloc, path, None, None, None))
		main_url = urllib.parse.urlunparse((self.scheme, self.netloc, "", None, None, None))
		query_kwargs = {query_parameter: "%d"}
		super().__init__(url = url, main_url = main_url)
		
	def search_anime(self, anime_english, anime_aliases = [], type_ = ""):
		return "found"

	#@Cache(prefix="NekoParser")
	def get_videos_list(self, anime_english, episode_num, type_ = "", anime_id = -1):
		if anime_id < 0:
			raise RuntimeError("anime_id must be provided")
			
		if not anime_id in shiki2neko:
			print("anime_id=%d cannot be converted to neko" % anime_id)
			return self.handler_epidode_not_found(anime_english, episode_num)
	
		neko_anime_id = shiki2neko[anime_id]
		neko_df = pd.read_json(os.path.join(app.config["DATAFRAMES_DIR"], "nekomori", "%d.txt" % neko_anime_id))
		if neko_df.empty:
			return self.handler_epidode_not_found(anime_english, episode_num)
	
		neko_df = neko_df.loc[neko_df['ep'] == episode_num]

		if neko_df.empty:
			return self.handler_epidode_not_found(anime_english, episode_num)

		videos_list = pd.DataFrame(columns = ["url", "episode", "kind", "quality", "video_hosting", "language", "author"])

		for index, row in neko_df.iterrows():
			quality = "Bluray" if row["bluray"] else "unknown"
			if row["status"] < 3 or row["kind"] == 0 or not row["author"]:
				continue
	
			link = row["link"]
			videos_list = videos_list.append({
				"url": link,
				"episode": str(episode_num),
				"video_hosting": row["player"] if row["player"] else urlparse(link).netloc,
				"author": row["author"],
				"quality": quality,
				"language": self.languages[row["language"]],
				"kind": self.to_db_kind[self.kinds[row["kind"]]]
			}, ignore_index = True)

		return videos_list
