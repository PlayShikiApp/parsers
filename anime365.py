import os
import urllib.request
import mechanize

from functools import lru_cache
from urllib.parse import urlencode, urlparse, urlunparse, quote_plus
from bs4 import BeautifulSoup
from parsers import ongoings
from parsers import parser
DATE_FORMAT = parser.DATE_FORMAT

class Anime365Parser(parser.Parser):
	headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.1144'}

	video_kinds = {
		"fandub": ["ozvuchka"],
		"subtitles": ["russkie-subtitry", "angliyskie-subtitry", "yaponskie-subtitry"],
		"raw": ["raw"]
	}
	def __init__(self, query_parameter = "q"):
		self.scheme = "https"
		self.netloc = "smotret-anime-365.ru"
		path = "/catalog/search"
		url = urllib.parse.urlunparse((self.scheme, self.netloc, path, None, None, None))
		main_url = urllib.parse.urlunparse((self.scheme, self.netloc, "", None, None, None))
		query_kwargs = {query_parameter: "%s", "undefined": "", "dynpage": "1"}

		super().__init__(url = url, main_url = main_url, headers = self.headers, query_kwargs = query_kwargs, query_parameter = query_parameter)
		self.setup_urlopener()

	def search_anime(self, anime_english):
		built_url = self.build_search_url(anime_english)

		page_name = "%s.html" % anime_english
		page_data = self.load_page(page_name)
		if not page_data:
			res = self.browser.open(built_url)
			redir_url = res.geturl()

			# if not found
			if "search" in redir_url:
				return None

			page_data = res.get_data()
			if not page_data:
				return None
		self.save_page(page_name, page_data)
		return page_data

	@lru_cache(maxsize = None)
	def get_episodes_list(self, anime_english):
		anime_page = self.search_anime(anime_english)
		if not anime_page:
			return self.handler_anime_not_found(anime_english)

		content = BeautifulSoup(anime_page, features = "html.parser")
		episodes_list = content.find("div", {"class": "m-episode-list"})

		if not episodes_list:
			return self.handler_episodes_list_not_found(anime_english)

		episodes = [a.get("href") for a in episodes_list.find_all("a", {"class": "m-episode-item"})]
		return {int(e.split("/")[-1].split("-")[0]): self.build_url(path = e) for e in episodes}

	@lru_cache(maxsize = None)
	def get_videos_list(self, anime_english, episode_num):
		episodes_list = self.get_episodes_list(anime_english)
		if not episode_num in episodes_list:
			return self.handler_epidode_not_found(anime_english, episode_num)

		anime_url = episodes_list[episode_num]

		videos_list = []
		for shiki_kind, kinds in self.video_kinds.items():
			for kind in kinds:
				page_name = os.path.join(anime_english, str(episode_num), shiki_kind, "%s.html" % kind)
				page_data = self.load_page(page_name)
				if not page_data:
					res = self.browser.open(os.path.join(anime_url, kind))
					page_data = res.get_data()
					self.save_page(page_name, page_data)
				content = BeautifulSoup(page_data, features = "html.parser")
				list_by_kind = [(self.build_url(path = a.get("href")), a.text) for a in content.find("div", {"class": "m-select-translation-list"}).find_all("a", {"class": "truncate"})]
				#print(videos_list)
				videos_list += list_by_kind
		return videos_list
