#!/usr/bin/python3-
import os, argparse, sqlite3
from sys import exit
from pathlib import Path
from datetime import datetime as dt

import paramiko
import feedparser

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
	pathHome = os.path.join(home, 'Music', 'podcasts/')
	

	subscheck = pod(curPass=curPass)
	for line in subscheck.subsRead():
		for i in line:
			if i.startswith('http'):
				l = encl_Feed(i)
	
				for attrib in l: #divides for episodeAdd()
					podPath = os.path.join(pathHome, attrib[0])
					fullLocation = os.path.join(podPath, attrib[1]+'.mp3')
					if not os.path.isfile(fullLocation): # checks whether file exists, sets dl to "No".
						dl="No"
						check = directoryCheck(podPath) #checks whether directory exists. 
						if not check:
							print("Error occured while making directories")
							exit()
					else:
						dl="yes"	


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
	fmt = dt.strftime(original, '%Y/%m/%d')
	return fmt

def subscriptionUpdater (connPass, curPass, args):
	'''
	Manages podcast subscriptions.
	'''

	if args.feed: #makes the use of args.name mandatory. 
		if args.name==None:
			print('Please enter a name for subscribing to a new series.')
			print('Usage: podcatch.py -f <"URL"> --name <"short name for series">')
			exit()

	subsData = pod(date=datefmt, series=args.name, src=args.feed, curPass = curPass, connPass=connPass)
	
	if args.feed:
		enscribe=ww(title='subs.txt', text=args.feed) #instantiates for txtWriter()
		enscribe.txtWriter() #appends whatever rss urls to subs.txt
		subsData.subsAdd() #needs feed already exists handling. :)
		print ("Subscription added! Database will update...please wait just a moment.")
		dataBasePopulate(connPass, curPass, args)
		print('Would you like to view the episodes?')
		eps = input('y/n: ')
		if eps.lower() == 'y':
			print('Ok!')
			
			seriesDownload(connPass, curPass, args)
				
	elif args.rfeed:
		subsView(subsData)
		if args.name == None:
			subsView(subsData)
			print('Please enter the name of the series to be removed.')
			print('Usage: podcatch.py -r --name <"short name for series">')
			exit()
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
		print(line)

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



def seriesDownload(connPass, curPass, args):
	'''
	Lists subscriptions, then episodes related to subscription numbered, finally
	passes to writer module and uses requests to download file.

	create way to update downloaded collumn in database. Check if functioning.
	'''

	sdl = pod(connPass=connPass, curPass=curPass)
	
	if args.name:
		series = args.name
		seriesFunc = sdl.seriesDownload(series)
	else:
		subsView(sdl)
		series=input("What series would you like to download from?: ")
		seriesFunc = sdl.seriesDownload(series)	
	
	for en, row in enumerate(seriesFunc):
		print ('''[{0}] {1}
	{2}\n'''.format(str(en), row[1], row[4])) 
	print('Which number(s) would you like to download (without brackets)? Separate with spaces:')	
	print('Press ctrl+c to exit.')
	try:
		number=input('> ')
	except KeyboardInterrupt:
		print("Goodbye.")
		exit()
	number=number.split(' ')
	verify(number)
	if not verify:
		print("Entry is not a number.")
		exit()

	for en, row in enumerate(sdl.seriesDownload(series)):	
		if str(en) in number:
			if not os.path.isfile(row[3]):	
				print('\n[+] {0}: {1} is downloading...'.format(row[0], row[1]))
				try:
					enscribe = ww(title=row[3], src=row[2])
					enscribe.fileWriter()
					sdl.episodeUpdate("yes", row[1])
					print('[+] Success!')
				except Exception as e:
					print('Error:\n{}'.format(str(e)))		
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

	print('Which number(s) would you like to download (without brackets)? Separate with spaces:')	
	print('Press ctrl+c to exit.')
	number = intCheckInput()

	for en, row in enumerate(passThru.episodeRecent()):
		if str(en) in number:
			if not os.path.isfile(row[3]):	
				print('\n[+] {0}: {1} is downloading...'.format(row[0], row[1]))
				
				try:	
					enscribe = ww(title=row[3], src=row[2])
					enscribe.fileWriter()
					passThru.episodeUpdate("yes", row[1])
					print('[+] Success!')
				except Exception as e:
					print('Error:\n{}'.format(str(e)))

			else:
				print('\n[-] {0}: {1} already exists at path {2}.'.format(row[0], row[1], row[3]))	


def verify(numlist):

	try:	
		verify=all(isinstance(int(item), int) for item in numlist)
		return verify
	except ValueError:
		print('A number wasn\'t entered!')
		return False

def intCheckInput():
	try:
		number=input("> ")
	except KeyboardInterrupt:
		print('Goodbye.')
		exit()
	number = number.split(' ')
	
	if number=='':
		print('Entry is not valid.')
		exit()

	verify(number)

	if not verify:
		exit()
	else:
		return number

def deleteTrack(connPass, curPass):
	track = pod(connPass=connPass, curPass=curPass)
	for en, row in enumerate(track.episodeOwn()):
		print('''[{0}] {1}
	{2}: {3}
	'''.format(str(en), row[0], row[2], row[1]))

	print('Which number(s) would you like to delete (without brackets)? Separate with spaces:')	
	print('Press ctrl+c to exit.')
	number = intCheckInput()

	for en, row in enumerate(track.episodeOwn()):
		if str(en) in number:
			print (row)
			
			if os.path.isfile(row[3]):
				print('\n[-] {0}: {1} has been removed.'.format(row[0], row[1]))
				try:
					os.unlink(row[3])
				except:
					print('An error Occured')	
				track.episodeUpdate('No', row[1])
				print('Done!')
			else:
				print('''\n[-] {0}: {1} does not exist at the indicated PATH.
			Was it moved or deleted by user or administrator?'''.format(row[0], row[1]))		
			

def currentPodcasts(connPass, curPass):
	current=pod(connPass=connPass, curPass=curPass)
	
	for en, row in enumerate(current.episodeOwn()):
		print('''[{0}]{1}
			{2} {3}'''.format(str(en), row[0], row[1], row[2]))

def trackCheck(connPass, curPass):
	track = pod(connPass=connPass, curPass=curPass)
	for row in track.episodeOwn():
		if os.path.isfile(row[3]):
			track.episodeUpdate('yes', row[1])
		else:
			track.episodeUpdate('No', row[1])	


def removeSeries(connPass, curPass, args):

	if not args.name:
		subsData=pod(connPass=connPass, curPass=curPass)
		subsView(subsData)
		print('Please enter the name of the series to be removed.')
		print('Usage: podcatch.py -remove --name <"short name for series">')
		exit()
	else:
		seriesList=pod(connPass=connPass, curPass=curPass, shortname=args.name)	
		print(
		"""This will remove all episodes from database and episode
			files from hard drive. Are you sure you want to continue?""")
		try:
			verify = input('ENTER to continue, ctrl+c to escape.')
		except KeyboardInterrupt:
			print('Goodbye!')
			exit()

		for row in seriesList.episodeOwn():
			try:
				if os.path.isfile(row[3]): os.unlink(row[3])
			except:
				print('Something Went Wrong!')	

		seriesList.seriesDelete()
		seriesList.subsDelete(args.name)

def sftpClient(host, port, username, passw=None, keypath=None, keypass=None):
	'''
	sftpClient is vehicle for sftp transfer of podcast files.
	'''
	try:
		if keypath!=None:
			key=paramiko.RSAKey.from_private_key_file(keypath, password=keypass)
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(host, port, username, passw, key)

		sftp = ssh.open_sftp()
		sftp.sshclient = ssh
		return sftp
	except Exception as e:
		print('An error occurred creating SFTP client: {0}: {1}'.format(e.__class__, e))	
		if sftp is not None:
			sftp.close()
		if ssh is not None:
			ssh.close()
		pass		

def trackSend(connPass, curPass, args):
	'''
	Takes a track and sends it over sftp to your android device.
	Saves it in /sdcard/Music/podcast/<shortname folder>
	'''
	print('''We are going to connect to your phone
	via ssh/sftp. Are we ready?''')
	
	confirm = input('Y/n: ')
	if confirm.lower() != "y" or 'yes':
		exit("Goodbye")
	
	if (args.port == None) and (args.host == None):
		print('Some nessary details were omitted.')
		print('usage: python3 podcatch.py --send --host "host" --port portnum --user "user" -k "keyname (e.g. id_rsa)"')
		exit('Bye')	
	else:	
		username, host, port = args.user, args.host, args.port

		if not args.pkey:	
			print('What\'s the password? Hit enter for private key entry.' )	
			password = input('Password: ')
			print('What\'s the key password? Hit enter if password entry.')
			keypass=input('Keypass: ')		
		else:
			password, keypass = '', args.pkey

		key=os.path.join(str(Path.home()), '.ssh', args.key)
		sftp_client = sftpClient(args.host, args.port, args.user, password, key, keypass)
		podcast = '/sdcard/Music'
		sftp_client.chdir(podcast)
		sdDir=sftp_client.listdir(podcast)
		pod_folder= os.path.join(podcast, 'podcasts')
		if 'podcasts' not in sdDir:
			sftp_client.mkdir('podcasts')	
		sftp_client.chdir(pod_folder)	

		current = currentPodcasts(connPass, curPass)

		print('Which numbers would you like to send?')
		print('Seperate selections with spaces.')
		number = intCheckInput()

		podList = sftp_client.listdir(pod_folder)	
		track = pod(connPass=connPass, curPass=curPass)	
		for en, row in enumerate(track.episodeOwn()):
			series_folder = os.path.join(pod_folder, row[4])
			if row[4] not in podList:
				sftp_client.mkdir(row[4])
			
			sftp_client.chdir(series_folder)
			if str(en) in number:
				try:
					print('Transfering: {}'.format(row[1]))
					sftp_client.put(row[3], os.path.join(series_folder, row[1]), confirm=True)
					print('Success!')
				except Exception as e:
					print('Err: {1}: {2}'.format(e.__class__, e))
			sftp_client.chdir(pod_folder)			

def trackRemove(connPass, curPass, args):
	print('''We are going to connect to your phone
	via ssh/sftp. Are we ready?''')
	
	confirm = input('Y/n: ')
	if confirm.lower() != "y" or 'yes':
		exit("Goodbye")
	
	if (args.port == None) and (args.host == None):
		print('Some nessary details were omitted.')
		print('usage: python3 podcatch.py --trackrem --host "host" --port portnum --user "user" -k "keyname (e.g. id_rsa)"')
		exit('Bye')	
	else:	
		username, host, port = args.user, args.host, args.port

		if not args.pkey:	
			print('What\'s the password? Hit enter for private key entry.' )	
			password = input('Password: ')
			print('What\'s the key password? Hit enter if password entry.')
			keypass=input('Keypass: ')		
		else:
			password, keypass = '', args.pkey

		key=os.path.join(str(Path.home()), '.ssh', args.key)
		sftp_client = sftpClient(args.host, args.port, args.user, password, key, keypass)
		podcast = '/sdcard/Music'
		sftp_client.chdir(podcast)
		sdDir=sftp_client.listdir(podcast)
		pod_folder= os.path.join(podcast, 'podcasts')
		if 'podcasts' not in sdDir:
			print('You currently don\'t have podcasts in the default dir.')
			exit('Goodbye') 	

		subs = pod(connPass=connPass, curPass=curPass)	
		
		for en, row in enumerate(subs.subsRead()):
			print('[{0}] {1}'. format(str(en), row[1]))
		print('From which series would you like to remove episodes?')
		print('Please separate selections with spaces')	
		number= intCheckInput()
		
		for en, row in enumerate(subs.subsRead()):
			folder = os.path.join(pod_folder, row[1])
			if en in number:
				if sftp_client.getcwd() != folder:
					sftp_client.chdir(folder)

				fileList = sftp_client.listdir(folder)
			
			for enum, f in enumerate(fileList):
				print("[{0}-{1}] {2}".format(str(en), str(enum), f))
				sftp_client.chdir(pod_folder)

		print('Which episodes would you like to remove?')
		print('Please use the n-n with a space between (e.g. 1-1 2-2 3-3)')		
		n0 = input("> ")
		n1=n0.split(" ")
		n2 = [n.split('-') for n in n1]  #should be [[1,1],[2,2]] etc.
			
		for n in n2:
			verify(n)
			if not verify:
				exit()

		for en, row in enumerate(subs.subsRead()):
			folder = os.path.join(pod_folder, row[1])
			for n in n2:	
				if en == n[0]:
					if sftp_client.getcwd() != folder:
						sftp_client.chdir(folder)
					
					fileList=sftp_client.listdir(folder)
					sftp_client.remove(fileList[n[1]])

		sftp_client.close()
		

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-f', dest='feed', help="Adds a new feed to the subscription list. Must be used with --name. -q is optional use. ")
	parser.add_argument('--name', dest='name', help='Identifies feed subscription by name you gave when subscribing. Names must be in quotation marks.')
	parser.add_argument('-r', dest='rfeed', help='Removes a feed from the subscription list. Must be in quotation marks.', action="store_true")
	parser.add_argument('--update', dest ='update', help='Checks for new updates. Can be used with -q', action='store_true')
	parser.add_argument('--view', dest='view', help='Displays current subscriptions.', action='store_true')
	parser.add_argument('-q', dest="verbose", action="store_true", help="Displays more information about what the database is doing.")
	parser.add_argument('--recent', dest='recent', help='Gets the most recent episode.', action='store_true')
	parser.add_argument('--load', dest='load', action='store_true', help='Loads urls of feeds into database from subs.txt file.')
	parser.add_argument('--series', dest='series', action='store_true', help='Displays all episodes of the series. Can be used with --name.')
	parser.add_argument('--tips', dest='tips', action='store_true', help='tips for podcatch use')
	parser.add_argument('--delete', dest='delete', action='store_true', help='Remove files from podcast collection.')
	parser.add_argument('--current', dest='current', action='store_true', help='Shows which files you currently have downloaded.')
	parser.add_argument('--check', dest='check', action='store_true', help='Resolves whether or not files are in database.')
	parser.add_argument('--remove', dest='remove', action='store_true', help='Removes complete series from hard drive and database. Use with caution. Must be used with --name.')
	parser.add_argument('--send', dest='send', action='store_true', help='Sends track to an ssh enabled device.')
	parser.add_argument('--host', dest='host', help='Host name for ssh server. Required with --ssh flag.')
	parser.add_argument('--port', dest='port', help='Port number for ssh server. Default is 22 if undeclared.', default=22)
	parser.add_argument('--user', dest='user', help='Username for ssh server. Default is user if undeclared.', default='user')
	parser.add_argument('--pkey', dest="pkey", help='Password for key encryption. If undeclared, it will be asked before connection.')
	parser.add_argument('-k', dest='key', default=None, help='Name of private key for passwordless access. Must be located in the .ssh dir of the home folder.')
	parser.add_argument('--rem', dest='rem', help='Removes user specified tracks from ssh android device.')
	args = parser.parse_args()

	
	if os.path.isfile('podcatch.py'):
		conn = sqlite3.connect('podbase.db')
		c = conn.cursor()
		tables=pod(connPass=conn, curPass=c)
		tables.subsTable()
		tables.episodeTable()
		trackCheck(conn, c)

		if args.feed or args.rfeed or args.view:
			subscriptionUpdater(conn, c, args)

		if args.update or args.recent or args.series:
			try:
				dataBasePopulate(conn, c, args)
			except Exception as e:
				print("Err: {0}: {1}".format(e.__class__, str(e)))

			if args.update:
				print("Would you like to see recent episodes?")
				rec = input("Y/n")
				if rec.lower() == 'y':
					recentEpsDL(conn, c)
			elif args.recent: 
				recentEpsDL(conn, c)
			elif args.series: 
				seriesDownload(conn, c, args)			

		if args.load: subLoad(conn, c)

		if args.delete: deleteTrack(conn, c)			

		if args.current: currentPodcasts(conn, c)
		
		if args.check: trackCheck(conn, c)

		if args.remove: removeSeries(conn, c, args)
		
		if args.send: trackSend(conn, c, args)

		c.close()
		conn.close()
	else:
		print('''
	The database is not in the current directory.
	Please move to the same directory for proper program function.''')
	
if __name__ == "__main__":
	main()
		