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

class Parser:
	to_db_kinds = {
                "fandub": "озвучка",
                "subtitles": "субтитры",
                "raw": "оригинал"
        }
	def __init__(self, url, main_url, headers = {}, query_kwargs = {}, query_parameter = "q"):
		if not hasattr(self, "scheme") or not hasattr(self, "netloc"):
			raise ValueError("Derived classes must set scheme and netloc atributes before invoking parent class")

		self.url = url
		self.main_url = main_url
		self.parsed_url = urllib.parse.urlparse(self.url)
		self.headers
		self.query_kwargs = query_kwargs
		self.query_parameter = query_parameter
		self.ensure_cache_dir_exists()
		return

	def ensure_cache_dir_exists(self):
		self.cache_root = os.path.join(CACHE_DIR, datetime.now().strftime(DATE_FORMAT))
		if not os.path.exists(self.cache_root):
			os.makedirs(self.cache_root)

	def get_page_path(self, page_name):
		site = self.netloc[1:] if self.netloc.startswith("/") else self.netloc
		return os.path.join(self.cache_root, site, page_name)

	def save_page(self, page_name, page_data):
		page_path = self.get_page_path(page_name)
		page_dirname = os.path.dirname(page_path)
		if not os.path.isdir(page_dirname):
			os.makedirs(page_dirname)
		open(page_path, "wb").write(page_data)

	def load_page(self, page_name):
		page_path = self.get_page_path(page_name)

		if not os.path.isfile(page_path) or os.stat(page_path).st_size == 0:
			return b""

		return open(page_path, "rb").read()

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

	def browser_open(self, url, retry_count = 5, retry_delay = 5):
		error_reason = ""
		for retry in range(retry_count):
			try:
				return self.browser.open(url)
			except urllib.error.URLError as e:
				error_reason = e.reason
				catch(error_reason)
			time.sleep(retry_delay)
		raise RuntimeError("Unable to open URL %s after %d retries" % (url, retry_count))

	def build_query(self, anime_english):
		query = self.query_kwargs.copy()
		query[self.query_parameter] = anime_english
		return query

	def build_url(self, scheme = "", netloc = "", path = "", params = None, query = None, fragment = None):
		scheme = scheme or self.scheme
		netloc = netloc or self.netloc
		return urllib.parse.urlunparse((scheme, netloc, path, params, query, fragment))

	def build_search_url(self, anime_english):
		query = self.build_query(anime_english)
		built_url = urllib.parse.urlunparse((self.parsed_url.scheme, self.parsed_url.netloc, self.parsed_url.path, None, urlencode(query, quote_via = quote_plus), None))
		return built_url

	def handler_anime_not_found(self, anime_english):
		print("Warning: anime \"%s\" was not found" % anime_english)
		return None

	def handler_episodes_list_not_found(self, anime_english):
		print("Warning: anime \"%s\" was found, but episodes list couldn't been retrieved" % anime_english)
		return None

	def handler_epidode_not_found(self, anime_english, episode_num):
		print("Warning: episode %d for anime \"%s\" couldn't been found" % (episode_num, anime_english))
		return None

	def handler_resource_is_unavailable(self):
		return None
