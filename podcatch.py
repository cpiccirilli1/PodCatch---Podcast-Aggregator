#!/usr/bin/python3
import os, argparse
from pathlib import Path
import sqlite3
from datetime import datetime as dt
#import feedparser
from writer import Writer as ww #personal module, use if you find useful.
from podDB import podData as pod #personal module, use if you find useful

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
	Need to make a way to ask for default save location.
	'''
	print('Updating Database... This may take a moment.')
	home=str(Path.home())
	path = os.path.join(home +'/Music/'+ 'podcasts/')
	

	subscheck = pod(curPass=curPass)
	for line in subscheck.subsRead():
		for i in line:
			if i.startswith('http'):
				l = encl_Feed(i)
	
				for attrib in l: #divides for episodeAdd()
					podPath = os.path.join(path, attrib[0])
					fullLocation = os.path.join(podPath, attrib[1]+'.mp3')
					if not os.path.isfile(fullLocation): # checks whether file exists, sets dl to "No".
						dl="No"
						check = directoryCheck(podPath) #checks whether directory exists. 
						if not check:
							return("Error occured while making directories: "+check[1])
					else:
						dl="Yes"	


					epDB = pod(downloaded=dl, shortname=line[1] ,published=dateConvert(attrib[3]), date=datefmt ,connPass=connPass, curPass=curPass, src=attrib[2], series=attrib[0], title=attrib[1], hdpath=fullLocation)
					epDB.episodeTable()
					epDB.episodeAdd()
					if args.verbose:
						print('[+] {0}: {1}'.format(attrib[1], attrib[2]))


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
	'''
	Converts date from original and returns fmt.
	'''
	original = dt.strptime(date, "%a, %d %b %Y %H:%M:%S %z")
	fmt = dt.strftime(original, '%Y/%m/%d %I:%M %p')
	return fmt

def subscriptionUpdater (args, connPass, curPass):
	'''
	Manages podcast subscriptions.
	'''
	if args.feed or args.rfeed or args.view:
		if args.feed: #makes the use of args.name mandatory. 
			if args.name==None:
				print('Please enter a name for subscribing to a new series.')
				print('Usage: podcatch.py -f <"URL"> --name <"short name for series">')
				return

		subsData = pod(date=datefmt, series=args.name, src=args.feed, curPass = curPass, connPass=connPass)
		
		if args.feed:
			enscribe=ww(title='subs.txt', text=args.feed) #instantiates for txtWriter()
			enscribe.txtWriter() #appends whatever rss urls to subs.txt
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
	'''
	Displays current subscriptions.
	'''
	for line in subsData.subsRead():
		print('[+] {0} added at {1}'.format(line[1], line[0]))

def subLoad(connPass, curPass):
	"""
	Updates subscriptions based on a text file list of url sources. 
	"""

	with open('subs.txt', 'r') as subs:
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

def numberCheck(number):
	for n in number:
		if not int(n):
			return False, n
		else:
			return True		

def seriesDownload(connPass, curPass):
	'''
	Lists subscriptions, then episodes related to subscription numbered, finally
	passes to writer module and uses requests to download file.

	create way to update downloaded collumn in database. Check if functioning.
	'''

	sdl = pod(connPass=connPass, curPass=curPass)
	subsView(sdl)
	series=input("What series would you like to download from?: ")
	for en, row in enumerate(sdl.seriesDownload(series)):
		print ('''[{0}] {1}
	{2}\n'''.format(str(en), row[1], row[4])) 

	number=input('Which number(s) would you like to download (without brackets)? Separate with spaces: ')
	number=number.split(' ')
	verify=numberCheck(number)

	if not verify[0]:
		print(verify[1])
		return

	for en, row in enumerate(sdl.seriesDownload(series)):	
		if str(en) in number:
			if not os.path.isfile(row[3])	
				enscribe = ww(title=row[3], src=row[2])
				enscribe.fileWriter()
				
				print('\n[+] {0}: {1} is downloading...'.format(row[0], row[1]))
				passThru.episodeUpdate("yes", row[1])	
			else:
				print('\n[-] {0}: {1} already exists at path {2}.'.format(row[0], row[1], row[3]))


def recentEpsDL(connPass, curPass):
	'''
	Displays last 10 episodes to be entered into database.

	Create way to update downloaded collumn in database. check if functioning.
	'''
	passThru = pod(connPass=connPass, curPass=curPass)
	for en, row in enumerate(passThru.episodeRecent()):
		print ('''[{0}] {1}
	{2} {3}\n'''.format(str(en), row[0], row[1], row[4]))

	number=input('Which number(s) would you like to download (without brackets)? Separate with spaces: ')
	number = number.split(' ')
	verify=numberCheck(number)

	if not verify[0]:
		print(verify[1])
		return

	for en, row in enumerate(passThru.episodeRecent()):
		if str(en) in number:
			if not os.path.isfile(row[3])	
				enscribe = ww(title=row[3], src=row[2])
				enscribe.fileWriter()
				
				print('\n[+] {0}: {1} is downloading...'.format(row[0], row[1]))
				passThru.episodeUpdate("yes", row[1])	
			else:
				print('\n[-] {0}: {1} already exists at path {2}.'.format(row[0], row[1], row[3]))	

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-f', dest='feed', help="Adds a new feed to the subscription list.")
	parser.add_argument('--name', dest='name', help='Identifies feed subscription by name you gave when subscribing. Names must be in quotation marks.')
	parser.add_argument('-r', dest='rfeed', help='Removes a feed from the subscription list. Must be in quotation marks.', action="store_true")
	parser.add_argument('--update', dest ='update', help='Checks for new updates.', action='store_true')
	parser.add_argument('-view', dest='view', help='Displays current subscriptions.', action='store_true')
	parser.add_argument('-q', dest="verbose", action="store_true", help="Displays more information about what the database is doing.")
	parser.add_argument('--recent', dest='recent', help='Gets the most recent episode.', action='store_true')
	parser.add_argument('--load', dest='load', action='store_true', help='Loads urls of feeds into database.')
	parser.add_argument('--test', dest='test', action='store_true', help='command for helping to test variables.')
	parser.add_argument('--tips', dest='test', action='store_true', help='tips for podcatch use')
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
		recentEpsDL(conn, c)

	if args.load:
		subLoad(conn, c)

	if args.test:
		seriesDownload(conn, c)		

	c.close()
	conn.close()

if __name__ == "__main__":
	main()
		