# author: @yoshinker

import re
import sys
import os
import requests
import getopt
import csv
from bs4 import BeautifulSoup
from mutagen.id3 import ID3, APIC, TIT2
from mutagen.id3 import ID3NoHeaderError

base_url = "https://downloads.khinsider.com"
album_url = ""
csv_file = ""
verbose = False
output_dir = "."

def usage():
	name = sys.argv[0]
	print("Description : python script to download music album from " + base_url)
	print("\nUSAGE :")
	print("\tpython " + name + " [OPTIONS] -u URL")
	print("\tpython " + name + " [OPTIONS] -c CSV_FILE")
	print("\nOPTIONS :")
	print("\t-h, --help : show help page")
	print("\t-v, --verbose : print download logs")
	print("\t-d OUTPUT_DIR, --directory=OUTPUT_DIR : specify output directory for downloaded files")
	print("\nURL FORMAT :")
	print("\thttps://downloads.khinsider.com/game-soundtracks/album/your_album")
	print("\nCSV FORMAT :")
	print("\tOUTPUT_DIR|URL")
	print("\nMade by @yoshinker, https://github.com/Yoshinker/ost_jv")

def main(argv):
	try:
		opts, args = getopt.getopt(argv, "hvu:d:c:", ["help", "verbose", "url=", "directory=", "csv="])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage()
			sys.exit()
		if opt in ("-v", "--verbose"):
			global verbose
			verbose = True
		if opt in ("-d", "--directory"):
			global output_dir
			output_dir = arg
		if opt in ("-u", "--url"):
			global album_url
			album_url = arg
		if opt in ("-c", "--csv"):
			global csv_file
			csv_file = arg

if __name__ == "__main__":
	main(sys.argv[1:])
	if (csv_file == "" and album_url == ""):
		usage()
		sys.exit(2)

download_list = list()

if csv_file != "":
	with open(csv_file, newline='') as f:
		reader = csv.reader(f, delimiter='|')
		for row in reader:
			download_list.append([row[0], row[1]])
else:
	download_list.append([output_dir, album_url])

#print(download_list)

for album in download_list:

	if not os.path.exists(album[0]):
		os.makedirs(album[0])

	main_page = requests.get(album[1])
	main_soup = BeautifulSoup(main_page.content, 'html.parser')

	# DOWNLOAD COVER
	cover = main_soup.find("img")
	if cover is not None and not re.search("album_views", cover['src']):
		cover_link = cover['src']
		r = requests.get(cover_link, allow_redirects=True)
		open(album[0] + "/cover.jpg", 'wb').write(r.content)
		imagedata = open(album[0] + '/cover.jpg', 'rb').read()

	#print(soup.prettify())

	songlist = main_soup.find(id="songlist")
	lines = songlist.find_all("tr")

	count = 1

	for l in lines:
		song = l.find("a")
		if song is not None:
			#print(song)
			#print(song_url)

			base_name = str(count) + ". " + song.get_text()
			song_name = str(count) + ". " + song.get_text()
			if not re.search("\.mp3$", song_name):
				song_name += ".mp3"

			song_url = base_url + song["href"]

			page = requests.get(song_url)
			soup = BeautifulSoup(page.content, 'html.parser')

			click = soup.find("a", text="Click here to download as MP3")

			if click is None:
				click = soup.findAll("span", {"class": "songDownloadLink"})[0].parent

			link = click["href"]

			#print(link)

			# DOWNLOAD
			path = album[0] + "/" + song_name

			if verbose:
				print("Downloading " + song_name + " ...")

			r = requests.get(link, allow_redirects=True)
			open(path, 'wb').write(r.content)

			if cover is not None and not re.search("album_views", cover['src']):

				try: 
				    id3 = ID3(path)
				except ID3NoHeaderError:
				    id3 = ID3()
				
				id3.add(TIT2(encoding=3, text=base_name))

				if not 'APIC' in id3:
					id3.add(APIC(3, 'image/jpeg', 3, 'Front cover', imagedata))

				id3.save(path)

			if verbose:
				print("Done!")
			
			count += 1