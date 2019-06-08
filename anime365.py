import os
import string
import urllib.request
import mechanize
import pandas as pd

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

	language_by_kind = {
		"ozvuchka": "russian",
		"russkie-subtitry": "russian",
		"angliyskie-subtitry": "english",
		"yaponskie-subtitry": "japanese",
		"raw": "japanese"
	}

	anime365_name_chars = string.ascii_letters + string.digits + " "

	def __init__(self, query_parameter = "q"):
		self.scheme = "https"
		self.netloc = "smotret-anime-365.ru"
		# for compatibility reasons
		self.netloc_alias = "smotretanime.ru"
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


	def search_anime(self, anime_english):
		built_url = self.build_search_url(anime_english)

		page_name = "%s.html" % anime_english
		page_data = self.load_page(page_name)
		if not page_data:
			res = self.browser.open(built_url)
			page_data = res.get_data()
			redir_url = res.geturl()

			# if not found
			if "search" in redir_url:
				results = BeautifulSoup(page_data, features = "html.parser").find_all("div", {"class": "m-catalog-item"})
				#print(len(results))
				if not results:
					return None

				found = False
				found_url = ""
				name = self.to_hosting_anime_name(anime_english = anime_english)
				for result in results:
					url = results[0].find("a").get("href")
					url_to_name = self.to_hosting_anime_name(url = url)
					#print(url_to_name, name)
					found = (url_to_name == name)
					if found:
						found_url = url
						break

				if not found:
					return None

				res = self.browser.open(self.build_url(path = found_url))

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

		videos_list = pd.DataFrame(columns = ["url", "episode", "kind", "quality", "video_hosting", "language", "author"])
		url_to_embed = lambda url: self.build_url(netloc = self.netloc_alias, path = "translations/embed/" + url.split("-")[-1])
		for shiki_kind, kinds in self.video_kinds.items():
			for kind in kinds:
				page_name = os.path.join(anime_english, str(episode_num), shiki_kind, "%s.html" % kind)
				page_data = self.load_page(page_name)
				b = BeautifulSoup(page_data)
				quality = "unknown"
				try:
					quality = max([int(a.text.split("(")[-1].split(")")[0][:-1]) for a in b.find("div", {"class": 'm-translation-view-download'}).find_all("a") if a.text.startswith("Скачать видео (")])
					quality = "%dp" % quality
				except AttributeError:
					pass

				if not page_data:
					res = self.browser.open(os.path.join(anime_url, kind))
					page_data = res.get_data()
					self.save_page(page_name, page_data)
				content = BeautifulSoup(page_data, features = "html.parser")
				list_by_kind = [(url_to_embed(url = a.get("href")), a.text) for a in content.find("div", {"class": "m-select-translation-list"}).find_all("a", {"class": "truncate"})]
				#print(videos_list)
				for a in content.find("div", {"class": "m-select-translation-list"}).find_all("a", {"class": "truncate"}):
					videos_list = videos_list.append({"url": url_to_embed(a.get("href")),
							    "episode": str(episode_num),
							    "video_hosting": self.netloc_alias,
							    "author": a.text,
							    "quality": quality,
							    "language": self.language_by_kind[kind],
							    "kind": shiki_kind
							   }, ignore_index = True)
		return videos_list
