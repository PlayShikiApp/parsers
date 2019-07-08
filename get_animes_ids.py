import os

from bs4 import BeautifulSoup
from percache import Cache

from . import misc
url_to_id = lambda url: int("".join([i for i in url.split("/")[-1].split("-")[0] if i.isdigit()]))

@Cache(prefix="get_animes_ids")
def get_animes_ids(target_folder = "animes"):
	res = []
	for page_file in os.listdir(target_folder):
		print(page_file)
		page_file = os.path.join(target_folder, page_file)
		h1 = BeautifulSoup(open(page_file).read(), features="html5lib")
		res += [url_to_id(a.find("a").get("href")) for a in h1.find_all("article")]

	return list(set(res))
