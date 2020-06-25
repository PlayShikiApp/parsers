#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

ALIASES = {
	"Detective Conan": ["Meitantei Conan", "Case Closed"],
	"JoJo no Kimyou na Bouken Part 5: Ougon no Kaze": ["JoJo no Kimyou na Bouken: Ougon no Kaze"],
	"Mangaka-san to Assistant-san to The Animation": ["Mangaka to assistant"],
	"Gintama.: Porori-hen": ["Gintama 6"],
	"Lord El-Melloi II Sei no Jikenbo: Rail Zeppelin Grace Note": ["Досье лорда"],
	"Sword Art Online: Alicization - War of Underworld": ["Мастера Меча Онлайн: Алисизация — Война в Подмирье"],
}

FORCE_ALIASES = {
	"anilibria": {
		"Kimi no Na wa.": "Твоё имя",
		"Gintama°": "", # Gintama 4
		"Gintama'": "", # Gintama 2
		"Gintama.": "", # Gintama 5
		"Gintama": "", # Gintama
		"Code Geass: Hangyaku no Lelouch R2": "Код Гиасс: Восстание Лелуша R2", # Code Geass: Hangyaku no Lelouch R2
		"One Punch Man": "Ванпанчмен",
		"Monster": "",
		"Natsume Yuujinchou Go": "",
		"Isekai Quartet": "Квартет из другого мира",
		"Fairy Tail: Final Series": "Сказка о Хвосте феи: Финал",
		"Fairy Gone": "Исход фей",
		"Nande Koko ni Sensei ga!?": "Учитель, почему Вы здесь?!",
		"Fruits Basket (2019)": "Корзинка с фруктами",
		"RobiHachi": "РобиХачи",
		"Kawaikereba Hentai demo Suki ni Natte Kuremasu ka?": "Полюбишь ли ты извращенку, если она милая?",
		"Shingeki no Kyojin Season 3 Part 2": "Атака титанов 3 (часть 2)",
		"Dumbbell Nan Kilo Moteru?": "Сколько кило тянешь?",
		"Black Clover": "Чёрный Клевер",
		"Cop Craft": "Ремесло копа",
		"Fairy Tail: Final Series": "Сказка о Хвосте феи (2018)",
		"Lord El-Melloi II Sei no Jikenbo: Rail Zeppelin Grace Note": "Досье лорда",
		"Re:Zero kara Hajimeru Isekai Seikatsu - Hyouketsu no Kizuna": "Re: Жизнь в другом мире с нуля - Замороженные узы",
		"Re:Zero kara Hajimeru Isekai Seikatsu - Memory Snow": "Re: Жизнь в другом мире с нуля - Снежные воспоминания",
		"Re:Zero kara Hajimeru Isekai Seikatsu: Memory Snow": "Re: Жизнь в другом мире с нуля - Снежные воспоминания"
	}
}

SKIP = [
	"Doraemon (2005)",
	"Chibi Maruko-chan (1995)",
	"Gudetama",
	"Sore Ike! Anpanman",
	"Xi Yang Yang Yu Hui Tai Lang",
	"Zhu Zhu Xia: Jing Qiu Xiao Yingxiong",
	"Xing You Ji: Fengbao Famila",
	"Papan Ga Panda!",
	"Crayon Shin-chan",
	"Detective Conan",
	"Sazae-san",
	"Nintama Rantarou"
]

MANUALLY_TRACKED_IDS = [
	269, # Bleach
	34572,
	39456,
	39198,
	36474,
	39597, # Sword Art Online: Alicization - War of Underworld
	36286,
	38414
]
