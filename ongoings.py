#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import asyncio
import urllib.request
import urllib.parse
import dateparser

from functools import lru_cache
from datetime import datetime
from bs4 import BeautifulSoup
from parsers.parser import DATE_FORMAT

ONGOING_IDS = []
OUT_DIR = ""

ANIME_TYPES = {
	"TV Сериал":	"tv",
	"ONA":		"ona",
	"OVA":		"ova",
	"Спешл":	"special"
}

def get_ongoing_id(article):
	ongoing_url = article.find("a").get("data-tooltip_url")
	return int(urllib.parse.urlparse(ongoing_url).path.split("/")[2].split("-")[0])

def fetch_all_ongoings(ids):
	OUT_DIR = datetime.now().strftime(DATE_FORMAT)
	if not os.path.exists(OUT_DIR):
		os.makedirs(OUT_DIR)
	total = len(ids)
	for n, id in enumerate(ids, start = 1):
		print("%d / %d" % (n, total))
		out_file = os.path.join(OUT_DIR, "%d.html" % id)

		if (os.stat(out_file).st_size == 0):
			print("file %d.html is empty" % id)

		if os.path.exists(out_file) and os.stat(out_file).st_size != 0:
			continue
		req = urllib.request.Request("https://shikimori.one/animes/%d" % id)
		open(out_file, "w").write(urllib.request.urlopen(req).read().decode("u8"))

def get_ongoing_info(id):
	return parse_ongoing(get_ongoing_html(id))

@lru_cache(maxsize = None)
def parse_ongoing(html):
	page = BeautifulSoup(html, features="html5lib")
	content = page.find("div", {"class": "l-content"})
	dateCreated = ""

	entry_info = content.find("div", "b-entry-info")
	entry_lines = [line.find("div", {"class": "line"}) for line in entry_info.find_all("div", {"class": "line-container"})]
	res = dict()
	for line in entry_lines:
		values = []
		if not line:
			continue
		for i in line.findAll(True, {"class": ["key", "value"]}):
			if not i.find("span"):
				values.append(i.text)
			else:
				values.append([j for j in i.strings if j])
		if len(values) == 2:
			res[values[0]] = values[1]

	res["episodes_available"], res["episodes_total"] = 0, 0
	if "Эпизоды:" in res:
		episodes = [i for i in res["Эпизоды:"].replace(" ", "").split("/")]

		if len(episodes) > 0:
			if episodes[0].isdigit():
				res["episodes_available"] = int(episodes[0])
		if len(episodes) > 1:
			if episodes[1].isdigit():
				res["episodes_total"] = int(episodes[1])


	res["next_episode"] = ""
	if "Следующий эпизод:" in res:
		next_episode_date = res["Следующий эпизод:"]
		try:
			res["next_episode"] = dateparser.parse(next_episode_date).strftime(DATE_FORMAT)
		except:
			pass

	res["type"] = ""
	if "Тип:" in res:
		if res["Тип:"] in ANIME_TYPES:
			res["type"] = ANIME_TYPES[res["Тип:"]]

	res["date_created"] = ""
	try:
		dateCreated = dateparser.parse(content.find("meta", {"itemprop": "dateCreated"}).get("content")).strftime(DATE_FORMAT)
		res["date_created"] = dateCreated
	except:
		pass

	res["anime_english"] = ""
	res["anime_russian"] = ""
	names = [i for i in page.find("h1").strings]
	if len(names) == 3:
		if names[0].endswith(" "):
			names[0] = names[0][:-1]

		if names[-1].startswith(" "):
			names[-1] = names[-1][1:]

		res["anime_russian"], res["anime_english"] = names[0], names[-1]

	return res

def get_ongoing_html(id):
	global OUT_DIR
	if not os.path.exists(OUT_DIR):
		os.makedirs(OUT_DIR)

	out_file = os.path.join(OUT_DIR, "%d.html" % id)
	if not os.path.exists(out_file) or os.stat(out_file).st_size == 0:
		if (os.stat(out_file).st_size == 0):
			print("file %d.html is empty" % id)
		req = urllib.request.Request("https://shikimori.one/animes/%d" % id)
		open(out_file, "w").write(urllib.request.urlopen(req).read().decode("u8"))
	return open(out_file, "r").read()

async def async_urlopen(req, out_file):
	open(out_file, "w").write(urllib.request.urlopen(req).read().decode("u8"))

async def get_ongoing_html_async(id):
	global QUEUE_LEN, ONGOING_IDS, OUT_DIR

	out_file = os.path.join(OUT_DIR, "%d.html" % id)
	try:
		if (os.stat(out_file).st_size == 0):
			print("file %d.html is empty" % id)

		if os.path.exists(out_file) and os.stat(out_file).st_size != 0:
			return
		req = urllib.request.Request("https://shikimori.one/animes/%d" % id)
		await async_urlopen(req, out_file)
	except:
		raise
	print("[%d / %d] %s" % (ONGOING_IDS.index(id) + 1, QUEUE_LEN, out_file))

async def coro(start, num_threads = 5):
	global ONGOING_IDS, QUEUE_LEN
	task_queue = ONGOING_IDS[start: min(start + num_threads, QUEUE_LEN)]
	tasks = [asyncio.ensure_future(get_ongoing_html_async(id)) for id in task_queue]
	await asyncio.wait(tasks)

def main(root_dir = "", start = 0, num_threads = 5, use_asyncio = False):
	global ONGOING_IDS, QUEUE_LEN, OUT_DIR
	if root_dir:
		os.chdir(root_dir)
	soup = BeautifulSoup(open("ongoings_07.06.2019.html", "r").read(), features="html5lib")
	articles = soup.find_all("article")
	ONGOING_IDS = [get_ongoing_id(a) for a in articles]
	QUEUE_LEN = len(ONGOING_IDS)

	OUT_DIR = datetime.now().strftime(DATE_FORMAT)
	if use_asyncio:
		ioloop = asyncio.get_event_loop()

		if not os.path.exists(OUT_DIR):
			os.makedirs(OUT_DIR)

		while start < QUEUE_LEN:
			ioloop.run_until_complete(coro(start, num_threads))
			start += num_threads
	else:
		fetch_all_ongoings(ONGOING_IDS)

if __name__ == "__main__":
	main()
