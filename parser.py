import urllib.request
import mechanize

from urllib.parse import urlencode, urlparse, urlunparse, quote_plus
from bs4 import BeautifulSoup

class Parser:
	def __init__(self, url, main_url, headers = {}, query_kwargs = {}, query_parameter = "q"):
		self.url = url
		self.main_url = main_url
		self.parsed_url = urllib.parse.urlparse(self.url)
		self.headers
		self.query_kwargs = query_kwargs
		self.query_parameter = query_parameter
		return

	def build_query(self, anime_english):
		query = self.query_kwargs.copy()
		query[self.query_parameter] = anime_english
		return query

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
		print("setup_urlopener: start")
		self.browser = mechanize.Browser()
		self.browser.set_handle_equiv(True)
		self.browser.set_handle_gzip(True)
		self.browser.set_handle_redirect(True)
		self.browser.set_handle_referer(True)
		self.browser.set_handle_robots(False)
		self.browser.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
		self.browser.addheaders = self.headers.items()

		url = url or self.main_url
		print("setup_urlopener: open url = %s" % url)
		#cookie = self.get_cookie(url)
		#if cookie:
		#	self.set_cookie(cookie)

	def build_url(self, anime_english):
		query = self.build_query(anime_english)
		built_url = urllib.parse.urlunparse((self.parsed_url.scheme, self.parsed_url.netloc, self.parsed_url.path, None, urlencode(query, quote_via = quote_plus), None))
		return built_url

	def handler_anime_not_found(self, anime_english):
		print("Warning: anime \"%s\" was not found" % anime_english)
		return None

	def handler_episodes_list_not_found(self, anime_english):
		print("Warning: anime \"%s\" was found, but episodes list couldn't have been retrieved" % anime_english)
		return None
