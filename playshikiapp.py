from parsers import ongoings

def main():
	ongoings.main()
	shiki_ongoing_data = ongoings.parse_ongoing(ongoings.get_ongoing_html(ongoings.ONGOING_IDS[0]))
	db_ongoing_info = routes.get_anime_info(ongoings.ONGOING_IDS[0])
	parser = Anime365Parser()
	parser.search_anime("Shingeki no Kyojin Season 3 Part 2")
