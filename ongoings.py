#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import asyncio
from datetime import datetime
import urllib.request
import urllib.parse

from bs4 import BeautifulSoup

from parsers import parser
DATE_FORMAT = parser.DATE_FORMAT

ONGOING_IDS = []
OUT_DIR = ""

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
		if os.path.exists(out_file):
				continue
		req = urllib.request.Request("https://shikimori.one/animes/%d" % id)
		open(out_file, "w").write(urllib.request.urlopen(req).read().decode("u8"))

def parse_ongoing(html):
	content = BeautifulSoup(html).find("div", {"class": "l-content"})
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

	if "Эпизоды:" in res:
		episodes = res["Эпизоды:"]
		res["episodes_available"], res["episodes_total"] = episodes.replace(" ", "").split("/")

	if "Следующий эпизод:" in res:
		next_episode_date = res["Следующий эпизод:"]
		res["next_episode"] = ""
		try:
			res["next_episode"] = dateparser.parse(next_episode_date).strftime(DATE_FORMAT)
		except:
			pass

	res["date_created"] = ""
	try:
		dateCreated = dateparser.parse(content.find("meta", {"itemprop": "dateCreated"}).get("content")).strftime(DATE_FORMAT)
		res["date_created"] = dateCreated
	except:
		pass

	return res

def get_ongoing_html(id):
	global OUT_DIR
	if not os.path.exists(OUT_DIR):
		os.makedirs(OUT_DIR)

	out_file = os.path.join(OUT_DIR, "%d.html" % id)
	if not os.path.exists(out_file):
		req = urllib.request.Request("https://shikimori.one/animes/%d" % id)
		open(out_file, "w").write(urllib.request.urlopen(req).read().decode("u8"))
	return open(out_file, "r").read()

async def async_urlopen(req, out_file):
	open(out_file, "w").write(urllib.request.urlopen(req).read().decode("u8"))

async def get_ongoing_html_async(id):
	global QUEUE_LEN, ONGOING_IDS, OUT_DIR

	out_file = os.path.join(OUT_DIR, "%d.html" % id)
	try:
		if os.path.exists(out_file):
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

def main(root_dir = "", start = 0, num_threads = 5, use_asyncio = True):
	global ONGOING_IDS, QUEUE_LEN, OUT_DIR
	if root_dir:
		os.chdir(root_dir)
	soup = BeautifulSoup(open("ongoings_07.06.2019.html", "r").read())
	articles = soup.find_all("article")
	ONGOING_IDS = [get_ongoing_id(a) for a in articles]
	QUEUE_LEN = len(ONGOING_IDS)

	if use_asyncio:
		ioloop = asyncio.get_event_loop()

		OUT_DIR = datetime.now().strftime(DATE_FORMAT)
		if not os.path.exists(OUT_DIR):
			os.makedirs(OUT_DIR)

		while start < QUEUE_LEN:
			ioloop.run_until_complete(coro(start, num_threads))
			start += num_threads
	else:
		fetch_all_ongoings(ONGOING_IDS)

if __name__ == "__main__":
	main()
