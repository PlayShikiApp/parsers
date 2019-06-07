#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
from datetime import datetime
import urllib.request
import urllib.parse

from bs4 import BeautifulSoup

def get_ongoing_id(article):
	ongoing_url = article.find("a").get("data-tooltip_url")
	return int(urllib.parse.urlparse(ongoing_url).path.split("/")[2].split("-")[0])

DATE_FORMAT = "%d.%m.%Y"

def fetch_all_ongoings(ids):
	out_dir = datetime.now().strftime(DATE_FORMAT)
	if not os.path.exists(out_dir):
		os.makedirs(out_dir)
	total = len(ids)
	for n, id in enumerate(ids, start = 1):
		print("%d / %d" % (n, total))
		out_file = os.path.join(out_dir, "%d.html" % id)
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
	out_dir = datetime.now().strftime(DATE_FORMAT)
	if not os.path.exists(out_dir):
		os.makedirs(out_dir)

	out_file = os.path.join(out_dir, "%d.html" % id)
	if not os.path.exists(out_file):
		req = urllib.request.Request("https://shikimori.one/animes/%d" % id)
		open(out_file, "w").write(urllib.request.urlopen(req).read().decode("u8"))
	return open(out_file, "r").read()

def main():
	os.chdir("/media/chrono/Windows1/d/dev/node/parsers")
	soup = BeautifulSoup(open("ongoings_07.06.2019.html", "r").read())
	articles = soup.find_all("article")
	ongoing_ids = [get_ongoing_id(a) for a in articles]
	fetch_all_ongoings(ongoing_ids)

if __name__ == "__main__":
	main()
