import urllib.request
import mechanize

from urllib.parse import urlencode, urlparse, urlunparse, quote_plus
from bs4 import BeautifulSoup
from parsers import ongoings
from parsers.parser import Parser

class Anime365Parser(Parser):
	headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.1144'}
	def __init__(self, query_parameter = "q"):
		self.scheme = "https"
		self.netloc = "smotret-anime-365.ru"
		path = "/catalog/search"
		url = urllib.parse.urlunparse((self.scheme, self.netloc, path, None, None, None))
		main_url = urllib.parse.urlunparse((self.scheme, self.netloc, "", None, None, None))
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
		return {int(e.split("/")[-1].split("-")[0]): e for e in episodes}

	def get_videos_list(self, anime_english, episode_num):
		anime_url = urllib.parse.urlunparse((self.scheme, self.netloc, path, None, None, None))
		res = self.browser.open("https://smotret-anime-365.ru/catalog/shingeki-no-kyojin-season-3-part-2-19608/1-seriya-195493")
		content = BeautifulSoup(res.get_data())
		videos_list = [(a.get("href"), a.text) for a in content.find("div", {"class": "m-select-translation-list"}).find_all("a", {"class": "truncate"})]
		return videos_list
