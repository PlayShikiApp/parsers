import urllib.request
import mechanize

from urllib.parse import urlencode, urlparse, urlunparse, quote_plus
from bs4 import BeautifulSoup
from shikimori import app, routes, models
from parsers import ongoings

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

class Anime365Parser(Parser):
	headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.1144'}
	def __init__(self, query_parameter = "q"):
		scheme = "https"
		netloc = "smotret-anime-365.ru"
		path = "/catalog/search"
		url = urllib.parse.urlunparse((scheme, netloc, path, None, None, None))
		main_url = urllib.parse.urlunparse((scheme, netloc, "", None, None, None))
		query_kwargs = {query_parameter: "%s", "undefined": "", "dynpage": "1"}

		super().__init__(url = url, main_url = main_url, headers = self.headers, query_kwargs = query_kwargs, query_parameter = query_parameter)

	def search_anime(self, anime_english):
		self.setup_urlopener()
		built_url = self.build_url(anime_english)
		res = self.browser.open(built_url)

		redir_url = res.geturl()

		# if not found
		if "search" in redir_url:
			return None

		return res
	
	def get_episodes_list(self, anime_english):
		res = self.search_anime(anime_english)
		if not res:
			return self.handler_anime_not_found(anime_english)

		anime_url = res.geturl()
		content = BeautifulSoup(res.get_data(), features = "html.parser")
		episodes_list = content.find("div", {"class": "m-episode-list"})

		if not episodes_list:
			return self.handler_episodes_list_not_found(anime_english)

		episodes = [a.get("href") for a in episodes_list.find_all("a", {"class": "m-episode-item"})]
		return episodes

	def get_videos_list(self, anime_english):
		res = self.browser.open("https://smotret-anime-365.ru/catalog/shingeki-no-kyojin-season-3-part-2-19608/1-seriya-195493")
		content = BeautifulSoup(res.get_data())
		videos_list = [(a.get("href"), a.text) for a in content.find("div", {"class": "m-select-translation-list"}).find_all("a", {"class": "truncate"})]
		return videos_list

def main():
	ongoings.main()
	shiki_ongoing_data = ongoings.parse_ongoing(ongoings.get_ongoing_html(ongoings.ONGOING_IDS[0]))
	db_ongoing_info = routes.get_anime_info(ongoings.ONGOING_IDS[0])
	parser = Anime365Parser()
	parser.search_anime("Shingeki no Kyojin Season 3 Part 2")
