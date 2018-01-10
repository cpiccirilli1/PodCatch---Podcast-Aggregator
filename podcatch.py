#!/usr/bin/python3
import os, argparse
from pathlib import Path
import sqlite3
from datetime import datetime as dt
import feedparser
from writer import Writer as ww
from podDB import podData as pod

datefmt = dt.strftime(dt.now(), '%Y/%m/%d %I:%M %p')


def encl_Feed(request):
	'''
	Gets xml doc from rss source. Checks for enclosure tags.
	Appends tuple to podList and returns. 
	'''
	podList = []
	ele = feedparser.parse(request)
	#ele2=feedparser.parse(request, etag=ele.etag)
	for e in ele.entries:
		if e.enclosures:
			podList.append((ele.feed.title, e.title, e.enclosures[0]['href'], e.published))						
	return podList		

def dataBasePopulate(connPass, curPass, args):
	'''
	Populates a database of episode (paths, titles, src, datepopulated, and others) from the subscriptions.
	Creates download locations and the file path to the future episode.
	Need to make a way to choose which you can get and ask for default save location.
	'''
	print('Updating Database... This may take a moment.')
	home=str(Path.home())
	path = os.path.join(home +'/Music/'+ 'podcasts/')
	

	subscheck = pod(curPass=curPass)
	for line in subscheck.subsRead():
		for i in line:
			if i.startswith('http'):
				l = encl_Feed(i)
	
				for attrib in l: #divides for writer.Writer() and episodeAdd()
					podPath = os.path.join(path, attrib[0])
					check = directoryCheck(podPath)
					podDir = os.listdir(podPath)
					fullLocation = os.path.join(podPath, attrib[1]+'.mp3')
			
					epDB = pod(shortname=line[1] ,published=dateConvert(attrib[3]), date=datefmt ,connPass=connPass, curPass=curPass, src=attrib[2], series=attrib[0], title=attrib[1], hdpath=fullLocation)
					epDB.episodeTable()
					epDB.episodeAdd()
					if args.verbose:
						print('[+] '+ attrib[1], attrib[2])
					'''
					if not check[0]:
						print('Something went wrong with creating directories: {}'.format(check[1]))	
					else:	
						if attrib[1] in podDir:
							print('[-] You already have that episode!')
						else:	
							pass
							#print('[+] '+ attrib[1], attrib[2])
							#writer = ww(title=fullLocation, src=attrib[2])
							#writer.fileWriter()
						'''
def directoryCheck(path):
	'''
	Checks to see if folder exists and if not
	creates all necessary folders in path. 
	'''

	if not os.path.isdir(path):
		try:	
			os.makedirs(path)
			return
		except OSError as e:
			return (False, 
				'A Problem Occured.')	
	return (True, 'No Error')	

def dateConvert(date):
	#"Wed, 07 Sep 2016 23:00:00 -0400"
	original = dt.strptime(date, "%a, %d %b %Y %H:%M:%S %z")
	fmt = dt.strftime(original, '%Y/%m/%d %I:%M %p')
	return fmt

def subscriptionUpdater (args, connPass, curPass):
	
	if args.feed or args.rfeed or args.view:
		if args.feed:
			if args.name==None:
				print('Please enter a name for subscribing to a new series.')
				print('Usage: podcatch.py -f <"URL"> --name <"short name for series">')
				return

		subsData = pod(date=datefmt, series=args.name, src=args.feed, curPass = curPass, connPass=connPass)
		
		if args.feed:
			subsData.subsAdd()
		elif args.rfeed:
			subsView(subsData)
			if args.name == None:
				print('Please enter the name of the series to be removed.')
				print('Usage: podcatch.py -r --name <"short name for series">')
				return
			else:
				try:
					subsData.subsDelete(args.name)
					print('{} subscription deleted.'.format(args.name))
				except:
					print('Invalid name: {}'.format(args.name))	
		elif args.view:
			subsView(subsData)
		else:
			pass		

def subsView(subsData):
	for line in subsData.subsRead():
				print('[+] {0} added at {1}'.format(line[1], line[0]))

def episodeView(passThru):
	
	for line in passThru.episodeRecent():
		print("[+]{0}".format(line))

def subLoad(connPass, curPass):
	"""
	Updates subscriptions based on a text file of url sources. 
	"""
	with open('subs', 'r') as subs:
		for line in subs:
			print(line)
			name = input('[+] Give me a shortname for the above feed: ')
			if name == "":
				print('[-] That is an unacceptable name.')
				break
			line2 = line.strip()
			subsData = pod(date=datefmt, series=name, src=line2, curPass = curPass, connPass=connPass)
			subsData.subsAdd()
			print ("[+] {0} has been added.".format(name))



def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-f', dest='feed', help="Adds a new feed to the subscription list.")
	parser.add_argument('--name', dest='name', help='Identifies feed subscription by name you gave when subscribing. Names must be in quotation marks.')
	parser.add_argument('-r', dest='rfeed', help='Removes a feed from the subscription list. Must be in quotation marks.', action="store_true")
	parser.add_argument('--update', dest ='update', help='Checks for new updates.', action='store_true')
	parser.add_argument('-v', dest='view', help='Displays current subscriptions.', action='store_true')
	parser.add_argument('-q', dest="verbose", action="store_true", help="Displays more information about what the database is doing.")
	parser.add_argument('--recent', dest='recent', help='Gets the most recent episode.', action='store_true')
	parser.add_argument('--load', dest='load', action='store_true', help='Loads urls of feeds into database.')
	args = parser.parse_args()

	conn = sqlite3.connect('podbase.db')
	c = conn.cursor()
	tables=pod(connPass=conn, curPass=c)
	tables.subsTable()
	tables.episodeTable()
	


	subscriptionUpdater(args, conn, c)

	if args.update:
		dataBasePopulate(conn, c, args)

	if args.recent:
		episodeView(tables)

	if args.load:
		subLoad(conn, c)	

	c.close()
	conn.close()

if __name__ == "__main__":
	main()
		