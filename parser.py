#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import sys
import time
import urllib.request, urllib.error
import mechanize

from datetime import datetime
from urllib.parse import urlencode, urlparse, urlunparse, quote_plus
from bs4 import BeautifulSoup
from parsers.tools import catch

DATE_FORMAT = "%d.%m.%Y"
CACHE_DIR = "parsers_cache"

MEDIA_KIND_VIDEOS = "videos"
MEDIA_KIND_TORRENTS = "torrents"

STATUS_EXISTS = 1

class Parser:
	to_db_kind = {
                "fandub": "озвучка",
                "subtitles": "субтитры",
                "raw": "оригинал"
        }

	attributes = [
		"scheme",
		"netloc",
		"fetch_latest_episode"
	]

	page_name_escape_chars = [":", "/", "?", "*"]

	name_match_threshold = 93
	supported_media_kinds = []

	def __init__(self, url, main_url, headers = {}, query_kwargs = {}, query_parameter = "q", abstract_class = False, anime_id = -1):
		if not abstract_class:
			for a in self.attributes:
				if not hasattr(self, a):
					raise ValueError("Derived classes must set %s attribute before invoking parent class" % a)

		self.url = url
		self.main_url = main_url
		self.parsed_url = urllib.parse.urlparse(self.url)
		self.headers
		self.query_kwargs = query_kwargs
		self.query_parameter = query_parameter
		self.ensure_cache_dir_exists()
		if not hasattr(self, "headers"):
			self.headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36"}
		return

	def is_media_kind_supported(self, media_kind):
		return media_kind in self.supported_media_kinds

	def ensure_cache_dir_exists(self):
		self.cache_root = os.path.join(CACHE_DIR, datetime.now().strftime(DATE_FORMAT))
		if not os.path.exists(self.cache_root):
			os.makedirs(self.cache_root)

	def get_page_path(self, page_name):
		site = self.netloc[1:] if self.netloc.startswith("/") else self.netloc
		return os.path.join(self.cache_root, site, page_name)

	def escape_page_name(self, page_name):
		return "".join([(i if not i in self.page_name_escape_chars else "_") for i in page_name])

	def save_page(self, page_name, page_data):
		page_path = self.get_page_path(self.escape_page_name(page_name))
		page_dirname = os.path.dirname(page_path)
		if not os.path.isdir(page_dirname):
			os.makedirs(page_dirname)
		open(page_path, "wb").write(page_data)

	def load_page(self, page_name):
		page_path = self.get_page_path(self.escape_page_name(page_name))

		if not os.path.isfile(page_path) or os.stat(page_path).st_size == 0:
			return b""

		return open(page_path, "rb").read()

	def load_or_save_page(self, page_name, url):
		page_data = self.load_page(page_name)
		if not page_data:
			try:
				res = self.browser_open(url)
			except RuntimeError:
				return self.handler_resource_is_unavailable()
			page_data = res.get_data()
			self.save_page(page_name, page_data)
		return page_data

	def get_cookie(self, url = ""):
		url = url or self.main_url
		opener = urllib.request.build_opener()
		req = urllib.request.Request(url, headers = self.headers)
		res = opener.open(req)
		cookie = res.headers.get('Set-Cookie')
		return cookie

	def set_cookie(self, cookie):
		self.browser.addheaders.append(("cookie", cookie))

	def setup_urlopener(self, url = ""):
		#print("setup_urlopener: start")
		self.browser = mechanize.Browser()
		self.browser.set_handle_equiv(True)
		self.browser.set_handle_gzip(True)
		self.browser.set_handle_redirect(True)
		self.browser.set_handle_referer(True)
		self.browser.set_handle_robots(False)
		self.browser.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
		self.browser.addheaders = self.headers.items()

		url = url or self.main_url
		#print("setup_urlopener: open url = %s" % url)
		#cookie = self.get_cookie(url)
		#if cookie:
		#	self.set_cookie(cookie)

	def handle_method(self, url, method, data):
		if (method == "GET"):
			return self.browser.open(url)
		if (method == "POST"):
			#request = mechanize.Request(url)
			#return mechanize.urlopen(request, data = bytes(urllib.parse.urlencode(data).encode()))
			req = urllib.request.Request(url)
			for k, v in self.headers.items():
				req.add_header(k, v)

			data = urllib.parse.urlencode(data).encode("u8")
			return urllib.request.urlopen(req, data = data)

	def browser_open(self, url, method = "GET", data = {}, retry_count = 5, retry_delay = 5):
		error_reason = ""
		for retry in range(retry_count):
			try:
				return self.handle_method(url, method, data)
			except Exception as e:
				error_reason = str(e.reason)
				catch("url=%s " % url + error_reason)
			time.sleep(retry_delay)
		raise RuntimeError("Unable to open URL %s after %d retries" % (url, retry_count))

	def build_query(self, anime_english, query_kwargs = {}):
		query = query_kwargs if query_kwargs else self.query_kwargs.copy()
		query[self.query_parameter] = anime_english
		return query

	def build_url(self, scheme = "", netloc = "", path = "", params = None, query = None, fragment = None):
		scheme = scheme or self.scheme
		netloc = netloc or self.netloc
		return urllib.parse.urlunparse((scheme, netloc, path, params, query, fragment))

	def build_search_url(self, anime_english = "", query_kwargs = {}, method = "GET"):
		query_kwargs = query_kwargs or self.build_query(anime_english, query_kwargs = query_kwargs)
		if method == "GET":
			built_url = urllib.parse.urlunparse((self.parsed_url.scheme, self.parsed_url.netloc, self.parsed_url.path, None, urlencode(query_kwargs, quote_via = quote_plus), None))
			return built_url
		if method == "POST":
			return urllib.parse.urlunparse((self.parsed_url.scheme, self.parsed_url.netloc, self.parsed_url.path, None, None, None)), query_kwargs

	def handler_anime_not_found(self, anime_english):
		print("Warning: anime \"%s\" was not found" % anime_english)
		return None

	def handler_authors_not_found(self, anime_english):
		print("Warning: couldn't determine authors (anime: \"%s\")" % anime_english)
		return None

	def handler_episodes_list_not_found(self, anime_english):
		print("Warning: anime \"%s\" was found, but episodes list couldn't been retrieved" % anime_english)
		return None

	def handler_epidode_not_found(self, anime_english, episode_num):
		print("Warning: episode %d for anime \"%s\" couldn't been found" % (episode_num, anime_english))
		return None

	def handler_epidode_exists(self, anime_english, episode_num, video_url):
		print("Warning: episode %d for anime \"%s\" already exists in the database, url = %s" % (episode_num, anime_english, video_url))
		return STATUS_EXISTS

	def handler_resource_is_unavailable(self):
		return None
