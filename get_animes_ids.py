from bs4 import BeautifulSoup
from percache import Cache

url_to_id = lambda url: int("".join([i for i in url.split("/")[-1].split("-")[0] if i.isdigit()]))

@Cache(prefix="get_animes_ids")
def get_animes_ids():
	res = []
	for i in range(1, 660):
		print(i)
		h1 = BeautifulSoup(open("animes/%d.html" % i).read(), features="html5lib")
		res += [url_to_id(a.find("a").get("href")) for a in h1.find_all("article")]

	return res
