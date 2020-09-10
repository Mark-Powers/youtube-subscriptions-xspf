#!/usr/bin/python3

import sys, datetime, re, itertools, multiprocessing, html, threading
import requests
from bs4 import BeautifulSoup

subscriptions = []
with open("subscription_manager.xml") as f:
	subs = BeautifulSoup(f.read(), "xml")
	for sub in subs.find_all("outline"):
		if "xmlUrl" in sub.attrs:
			subscriptions.append(sub["xmlUrl"])

def get_videos(channel):
	tracks = []
	print ("=", end="", flush=True)
	r = requests.get(channel)
	updates = BeautifulSoup(r.text.encode(sys.stdout.encoding, errors='replace'), "xml")
	for entry in updates.find_all("entry")[:3]:
		if entry.title and entry.link:
			item = {}
			item["title"] = html.escape(entry.title.string if entry.title.string else "")
			item["link"] = entry.link["href"]
			item["channel"] = html.escape(entry.author.find("name").string)
			date_string = entry.published.string.split("T")[0]
			item["date"] = date_string
			date = datetime.datetime.strptime(date_string, "%Y-%m-%d")
			today = datetime.datetime.today()
			margin = datetime.timedelta(days = 7)
			if today-margin <= date:
				tracks.append(item)
	return tracks

def get_entry(item, index):
	string = ("\t<track>\n\t\t<location>"+item["link"]+"</location>\n" +
		  "\t\t<title>"+item["title"]+ "</title>\n" +
		  "\t\t<creator>" + item["channel"] + "</creator>\n" +
		  "\t\t<album>" + item["date"] + "</album>\n" +
		  "\t</track>\n")
	return re.sub(r'[^\x00-\x7F]+',' ', string)

def main():
	tracks = []
	with multiprocessing.Pool(4) as p:
		print("[ " + " "*len(subscriptions)+ "]",end="\r[=", flush=True)
		videos = p.map(get_videos, subscriptions)
		tracks = list(itertools.chain.from_iterable(videos))
		print()

	with open("subscriptions.xspf", "w") as f:
		file_tail = '</trackList>\n'
		f.write('''<?xml version="1.0" encoding="UTF-8"?>
		<playlist xmlns="http://xspf.org/ns/0/" xmlns:vlc="http://www.videolan.org/vlc/playlist/ns/0/" version="1">
			<title>Subscriptions</title>
			<trackList>\n''')
		for item in enumerate(tracks):
			f.write(get_entry(item[1], item[0]))
		file_tail += '</playlist>\n'
		f.write(file_tail)
	print("Done")

if __name__ == '__main__':   
	main()
