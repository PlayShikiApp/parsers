import sys
import pickle
import pandas as pd

from functools import lru_cache
from sqlalchemy import create_engine

from parsers import ongoings, anime365
from parsers.tools import catch
from shikimori import routes, models

def import_to_db(from_pickle = False):
	engine = create_engine(open(".env").read(), echo=True)
	index = routes.get_index(models.AnimeVideo)

	if not from_pickle:
		result = find_all_ongoings()
	else:
		result = pickle.load(open("ongoings.pkl", "rb"))

	result["id"] = range(index + 1, index + len(result)  + 1)
	result.to_sql(name='anime_videos', con=engine, if_exists = 'append', index=False)

def save(from_pickle = False, format = "pkl"):
	if not from_pickle:
		result = find_all_ongoings()
	else:
		result = pickle.load(open("ongoings.pkl", "rb"))

	if format == "pkl":
		pickle.dump("ongoings.pkl", "wb")

def find_all_ongoings(parsers = {"smotretanime": anime365.Anime365Parser}):
	ongoings.main()
	ongoings.ONGOING_IDS = ongoings.ONGOING_IDS

	result = pd.DataFrame(columns = ["anime_id", "anime_english", "anime_russian", "watches_count", "uploader", "url", "episode", "kind", "quality", "language", "author"])
	for hosting, Parser in parsers.items():
		parser = Parser()
		total = len(ongoings.ONGOING_IDS)
		for n, id in enumerate(ongoings.ONGOING_IDS, start = 1):
			note = "found"
			shiki_ongoing_data = {}
			try:
				anime_info = routes.get_anime_info(id)
			except:
				catch()
				shiki_ongoing_data = ongoings.parse_ongoing(ongoings.get_ongoing_html(id))
				#anime_info = {}
				note = "not found in database, skipping for now"
				print("[%d / %d] %s: %s" % (n, total, anime_info["anime_english"], note))
				continue

			if not parser.search_anime(anime_info["anime_english"]):
				note = "not found"
				print("[%d / %d] %s: %s" % (n, total, anime_info["anime_english"], note))
				continue

			max_episode = routes.get_max_episode_for_hosting(id, hosting)
			if not shiki_ongoing_data:
				shiki_ongoing_data = ongoings.parse_ongoing(ongoings.get_ongoing_html(id))
			if shiki_ongoing_data["episodes_available"] <= max_episode:
				note = "already fetched all available episodes"
				print("[%d / %d] %s: %s" % (n, total, anime_info["anime_english"], note))
				continue

			print("[%d / %d] %s: %s" % (n, total, anime_info["anime_english"], note))
			tmp_videos_list = pd.DataFrame(columns = ["url", "episode", "kind", "quality", "video_hosting", "language", "author"])
			for episode_num in range(max_episode + 1, shiki_ongoing_data["episodes_available"] + 1):
				df = parser.get_videos_list(anime_info["anime_english"], episode_num)
				if (isinstance(df, type(None))) or df.empty:
					note = "no videos found"
					print("[%d / %d] %s (%d / %d): %s" % (n, total, anime_info["anime_english"], episode_num, shiki_ongoing_data["episodes_available"], note))

				
				print("[%d / %d] %s (%d / %d)" % (n, total, anime_info["anime_english"], episode_num, shiki_ongoing_data["episodes_available"]))
				tmp_videos_list = tmp_videos_list.append(df, ignore_index = True, sort = False)

			tmp_videos_list["anime_id"] = str(id)
			tmp_videos_list["anime_english"] = anime_info["anime_english"]
			tmp_videos_list["anime_russian"] = anime_info["anime_russian"]
			tmp_videos_list["watches_count"] = "0"
			tmp_videos_list["uploader"] = "importbot"
			del tmp_videos_list["video_hosting"]
			result = result.append(tmp_videos_list, ignore_index = True, sort = False)
	return result
