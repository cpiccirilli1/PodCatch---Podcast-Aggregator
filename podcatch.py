#!/usr/bin/python3
'''
version 0.9.3
MIT License
'''

import os, argparse, sqlite3
from sys import exit
from pathlib import Path
from datetime import datetime as dt
import platform
import paramiko
import feedparser
from writer import Writer as ww #personal module, use if you find useful.
from podDB import podData as pod #personal module, use if you find useful

datefmt = dt.strftime(dt.now(), '%Y/%m/%d %I:%M %p')

class pod_parse:

	def __init__(self, request=None):
		self.request = request

	def _title_info(self):
		pod_info = []
		try:
			element = feedparser.parse(self.request) #instantiates feedparser object
			pod_info.append(element.feed.title, element.feed.description, element.feed.link) #appends info for db table use later
			return pod_info
		except AttributeError as e:
			print('The following error occured. Usually due to an inability to access the network.')

	def _feed_parse(self):
		ele = feedparser.parse(self.request)
		et, ele2 =self._etag(ele)
		last, ele3 = self._last_mod(ele)
		
		if et:
			return [ele2.debug_message]
		elif last:
			return [ele3.debug_message]		
		else:
			if 'enclosures' in ele.entries[0]:				
				chopFeed = self._encl_Feed(ele)
			else:
				chopFeed = self._reg_feed(ele)
		return chopFeed		

	def _reg_feed(self, elePass):
		podList = []
		for e in elePass.entries:
			tupList = ()
			 
			if 'title' in elePass.feed: 
				tupList += (elePass.feed.title,)
			else:
				tupList += (None,)	
			if 'title' in e: 
				tupList += (e.title,)
			else:
				tupList += (None,)		  
			if 'href' in e['links'][1]: 
				tupList += (e['links'][1]['href'],)
			else:
				tupList += (None,)	
			if e.published: 
				tupList += (e.published,)
			else:
				tupList += (None,)	
			if e.description: 
				tupList += (e.description,)
			else:
				tupList += (None,)

			if len(tupList) == 5: 
				podList.append(tupList)
			else:
				podList.append('Insufficient Data!')
		return podList

	def _encl_Feed(self, elePass):
		'''
		Gets xml doc from rss source. Checks for enclosure tags.
		Appends tuple to podList and returns. 
		request: requested url from server 
		type: string
		rtype: list
		'''
		
		podList = []
		for e in elePass.entries:
			tupList = ()
			if e.enclosures: 
				if 'title' in elePass.feed: 
					tupList += (elePass.feed.title,)
				else:
					tupList += (None,)	
				if 'title' in e: 
					tupList += (e.title,)
				else:
					tupList += (None,)		  
				if 'href' in  e.enclosures[0]: 
					tupList += (e.enclosures[0]['href'],)
				else:
					tupList += (None,)	
				if e.published: 
					tupList += (e.published,)
				else:
					tupList += (None,)	
				if e.description: 
					tupList += (e.description,)
				else:
					tupList += (None,)
			else:
				pass

			if len(tupList) == 5: 
				podList.append(tupList)
			else:
				podList.append('Insufficient Data!')

		return podList
			
	def _etag(self, element):
		if 'etag' in element.headers:
			element2 = feedparser.parse(self.request, etag=element.etag)	
			if element2.status == 304: 			
				return True, element2
			else:
				return False, element	
		else: 
			return False, element

	def _last_mod(self, element):
		if 'last-modified' in element.headers:
			element2 = feedparser.parse(self.request, modified=element.modified)	
			if element2.status == 304: 
				return True, element2
			else:
				return False, element	
		else: 
			return False, element	

	def _etag_lastmod(self, row):
		if len(row) < 2:
			print(row[0])		
			return True	
		else:
			return False

def dataBasePopulate(connPass, curPass, args):
	'''
	Populates a database of episode (paths, titles, src, datepopulated, and others) from the subscriptions.
	Creates download locations and the file path to the future episode.
	Need to make a way to ask for default save location.
	connPass: connection pass through
	type: variable
	curPass: cursor pass through
	type: variable
	args: args pass through
	type: variable
	rtype: None
	'''
	print('Updating Database... This may take a moment.')
	home=str(Path.home())
	pathHome = os.path.join(home, 'Music', 'podcasts/')

	subscheck = pod(curPass=curPass)
	for line in subscheck.subsRead():
		for i in line:
			if i.startswith('http'):
				pp = pod_parse(i)
				l = pp._feed_parse()
				etag = pp._etag_lastmod(l)
				if etag: 
					break
				else:
					loadCount = 0
					errCount = 0
					for attrib in l: #divides for episodeAdd()
						podPath = os.path.join(pathHome, attrib[0])
						fullLocation = os.path.join(podPath, attrib[1]+'.mp3')
						if not os.path.isfile(fullLocation): # checks whether file exists, sets dl to "No".
							dl="No"
							check, message = _directoryCheck(podPath) #checks whether directory exists. 						
						else:
							dl="yes"	
	
						try:								
							dateCon = _dateConvert(attrib[3])								
							epDB = pod(desc=attrib[4], downloaded=dl, shortname=line[1] ,published=dateCon, date=datefmt ,connPass=connPass, curPass=curPass, src=attrib[2], series=attrib[0], title=attrib[1], hdpath=fullLocation)
							epDB.episodeTable()
							epDB.episodeAdd()
							loadCount  +=  1
							if args.verbose: print('[+] {0}: {1}'.format(attrib[1], attrib[2]))
						except Exception as e:
							errCount  +=  1
							print ('Upload Err: {0}: {1}'.format(str(e.__class__), str(e)))

					if errCount != 0: print("{}/{} failed".format(errCount, loadCount))		
			else:
				pass 			



def _directoryCheck(path):
	'''
	Checks to see if folder exists and if not
	creates all necessary folders in path. 
	path: path to check for existence of
	type: string
	'''

	if not os.path.isdir(path):
		try:	
			os.makedirs(path)
			return (True, "{0} was made.".format(path))
		
		except OSError as e:
			return (False, 'Error Occured.')
	else:				
		return (False, 'False.')	

def _dateConvert(date):
	'''
	Converts date from original and returns fmt.
	date: date object from datetime.datetime.now()
	type: string
	'''
	
	original = dt.strptime(date, "%a, %d %b %Y %H:%M:%S %z")
	try:
		fmt = dt.strftime(original, '%Y/%m/%d')
		return fmt
	except Exception as e:
		pass

class Subscriptions:

	def __init__(self, connectP = None, cursorP = None, args=None):

		self.connectP = connectP
		self.cursorP = cursorP
		self.args = args
			
	def subscriptionUpdater(self):
		'''
		Manages podcast subscriptions.
		connPass: connection pass through
		type: variable
		curPass: cursor pass through
		type: variable
		args: args pass through
		type: variable	
		'''

		if self.args.feed or self.args.rfeed: #makes the use of args.name mandatory. 
			if self.args.name==None:
				print('Please enter a name for adding/removing a series.')
				print('Add Usage: podcatch.py -f <"URL"> --name <"short name for series">')
				print('Remove Usage: podcatch.py -r <"URL"> --name <"short name for series">')
				exit()
			else:
				pass	
		else:
			subsData = pod(date=datefmt, series=self.args.name, src=self.args.feed, curPass = self.cursorP, connPass=self.connectP)
		
		if self.args.feed:
			self.add_feed()			
		elif self.args.rfeed:
			self.remove_feed(subsData)	
		elif self.args.view:
			self.subsView(subsData)
		else:
			pass		

	def add_feed(self):
		info = pod_parse._title_info(self.args.feed)
		subs_info = pod(title=info[0], desc=info[1], date=datefmt, series=self.args.name, src=self.args.feed, curPass = self.curPass, connPass=self.connPass)
		enscribe=ww(title='subs.txt', text=self.args.feed+'\n') #instantiates for txtWriter()
		if not os.path.isfile('subs.txt'):
			enscribe.txtWriter()
		else:	
			enscribe.txtWriter(mode='a') #appends whatever rss urls to subs.txt
		
		subs_info.subsAdd() 
		print ("Subscription added! Database will update...please wait just a moment.")
		dataBasePopulate(self.connectP, self.cursorP, self.args)
		print('Would you like to view or download the episodes?')
		eps = input('Y/n: ')
		if eps.lower() != 'y':
			exit()
		else:	
			print('Ok!')
			dl = Downloading(connP=self.connectP, curP=self.cursorP, args=self.args)
			dl.seriesDownload()
			
	def remove_feed(self, subsData):
		print('Would you like to delete the episodes as well?')
		eps_delete=input('Y/n')
		if eps_delete.lower() == 'n' or 'no':
			try:
				subsData.subsDelete(self.args.name)
				print('{} subscription deleted.'.format(self.args.name))
			except:
				print('Invalid name or subscription doesn\'t exist: {}'.format(self.args.name))	
		elif eps_delete.lower() == 'y' or 'yes':
				self.removeSeries()
		else:
			print('You have entered an invalid answer. Goodbye.')
			exit()		

	def subsView(self, subsData):
		'''
		Displays current subscriptions.
		subsData: instantiation pass through
		'''
		for line in subsData.subsRead():
			if self.args.verbose:
				print('''
	[+] {0}: {1} 
	{2}	'''.format(line[1], line[2], line[4])
					)
			else:	
				print('[+] {0} added on {1}'.format(line[1], line[0]))

	def subLoad(self):
		"""
		Updates subscriptions based on a text file list of url sources. 
		connPass: connection pass through
		type: variable
		curPass: cursor pass through
		type: variable	
		"""

		with open('subs.txt', 'r') as subs:
			for line in subs:
				if line != '\n':
					print(line)
					name = input('[+] Give me a shortname for the above feed: ')
					if name == "":
						print('[-] That is an unacceptable name.')
						break
					else:						
						line2 = line.strip()
						feed = pod_parse(line2)
						info = feed._title_info()
						subsData = pod(date=datefmt, title=info[0], desc=info[1],  series=name, src=line2, curPass = self.cursorP, connPass=self.connectP)
						subsData.subsAdd()
						print ("[+] {0} has been added.".format(name))
				else:
					print("Empty line. :(")

	def removeSeries(self):
		'''
		removes an entire series mp3 tracks and database entries.
		connPass: connection pass through
		type: variable
		curPass: cursor pass through
		type: variable
		args: args pass through
		type: variable
		'''
		if not self.args.name:
			subsData=pod(connPass=self.connectP, curPass=self.cursorP)
			self.subsView(subsData)
			print('Please enter the name of the series to be removed.')
			print('Usage: podcatch.py -remove --name <"short name for series">')
			exit()
		else:
			seriesList=pod(connPass=self.connectP, curPass=self.cursorP, shortname=self.args.name)	
			print(
			"""This will remove all episodes from database and episode
				files from hard drive. Are you sure you want to continue?""")
			try:
				verify = input('ENTER to continue. Type "exit" or press ctrl+c to quit.')
			except KeyboardInterrupt:
				print('Goodbye!')
				exit()

			if verify.lower() != 'exit':	

				for row in seriesList.episodeOwn():
					try:
						if os.path.isfile(row[3]): 
							os.unlink(row[3])
						else:
							pass	
					except:
						print('Something Went Wrong!')	

				seriesList.seriesDelete()
				seriesList.subsDelete(self.args.name)
			else:
				print('Goodbye')
				exit()							

class Downloading:
	def __init__(self, connP = None, curP = None, args = None):

		self.connP = connP
		self.curP = curP
		self.args = args
		
	def db_conn(self):
		pod_DB = pod(connPass=self.connP, curPass=self.curP)
		return pod_DB

	def seriesDownload(self):
		'''
		Lists subscriptions, then episodes related to subscription numbered, finally
		passes to writer module and uses requests to download file.
		connPass: connection pass through
		type: variable
		curPass: cursor pass through
		type: variable
		args: args pass through
		type: variable
		'''
		
		if self.args.name:
			seriesFunc = self.db_conn().seriesDownload(self.args.name)
		else:
			subs = Subscriptions(connectP=self.connP, cursorP=self.curP, args=self.args)
			subs.subsView()
			series=input("What series would you like to download from?: ")
			seriesFunc = self.db_conn().seriesDownload(series)	
		
		for en, row in enumerate(seriesFunc):
			print ('''[{0}] {1}
		{2}\n'''.format(str(en), row[1], row[4])) 
		print('Which number(s) would you like to download (without brackets)? Separate with spaces:')	
		print('Press ctrl+c or type "exit" to exit.')
		number = intCheckInput()

		for en, row in enumerate(seriesFunc):	
			if str(en) in number:
				if not os.path.isfile(row[3]):	
					print('\n[+] {0}: {1} is downloading...'.format(row[0], row[1]))
					try:
						enscribe = ww(title=row[3], src=row[2])
						enscribe.fileWriter()
						self.db_conn().episodeUpdate("yes", row[1])
						print('[+] Success!')
					except ConnectionError as e:
						print('Error:\n{}'.format(str(e)))		
				else:
					print('\n[-] {0}: {1} already exists at path {2}.'.format(row[0], row[1], row[3]))
			else:
				pass		

	def recentEpsDL(self):
		'''
		Displays last 10 episodes to be entered into database that are currently not in your possession.
		Create way to update downloaded collumn in database. check if functioning.
		'''
		passThru = self.db_conn().episodeRecent()
		for en, row in enumerate(passThru):
			if row not in self.db_conn().episodeOwn():

				if self.args.verbose:
					print(
	'''[{0}] {1}
	{2} {3}
	{4}\n
	'''.format(str(en), row[0], row[1], row[4], row[7])
					)
				else:	
					print (
	'''[{0}] {1}
	{2} {3}\n'''.format(str(en), row[0], row[1], row[4]))
			else:
				pass		
		print('Which number(s) would you like to download (without brackets)? Separate with spaces:')	
		print('Press ctrl+c or type "exit" to exit.')
		number = intCheckInput()

		for en, row in enumerate(self.db_conn().episodeRecent()):
			if str(en) in number:
				if not os.path.isfile(row[3]):	
					print('\n[+] {0}: {1} is downloading...'.format(row[0], row[1]))
					
					try:	
						enscribe = ww(title=row[3], src=row[2])
						enscribe.fileWriter()
						passThru.episodeUpdate("yes", row[1])
						print('[+] Success!')
					except ConnectionError as e:
						print('Error:\n{0}, {1}'.format(str(e.__class__),str(e)))
						exit()

				else:
					print('\n[-] {0}: {1} already exists at path {2}.'.format(row[0], row[1], row[3]))	
			else:
				pass

	def deleteTrack(self):
		track = self.db_conn()
		for en, row in enumerate(track.episodeOwn()):
			print('''[{0}] {1}
		{2}: {3}
		'''.format(str(en), row[0], row[2], row[1]))

		print('Which number(s) would you like to delete (without brackets)? Separate with spaces:')	
		print('Press ctrl+c or type "exit" to exit.')
		number = intCheckInput()

		for en, row in enumerate(track.episodeOwn()):
			if str(en) in number:
				
				if os.path.isfile(row[3]):
					print('\n[-] {0}: {1} has been removed.'.format(row[0], row[1]))
					try:
						os.unlink(row[3])
						track.episodeUpdate('No', row[1])
					except:
						print('An error Occured')	
					
					print('Done!')
				else:
					print('''\n[-] {0}: {1} does not exist at the indicated PATH.
				Was it moved or deleted by user or administrator?'''.format(row[0], row[1]))		
			
			else:
				pass	

def _verify(numlist):

	try:	
		verify=all(isinstance(int(item), int) for item in numlist)
		return verify
	except ValueError:
		print('A number wasn\'t entered!')
		return False

def intCheckInput():
	try:
		number = input("> ")
	except KeyboardInterrupt:
		print('Goodbye.')
		exit()
	number = number.split(' ')
	
	if number == '':
		print('Entry is not valid.')
		exit()
	elif number == 'exit':
		print("Goodbye")
		exit()	
	else:
		ver=_verify(number)

	if not ver:
		exit()
	else:
		return number


def currentPodcasts(connectPass, cursorPass):
	current = pod(connPass=connectPass, curPass=cursorPass)
	print('These are your current tracks.')
	for en, row in enumerate(current.episodeOwn()):
		print('''[{0}]{1}
		{2} {3}'''.format(str(en), row[0], row[1], row[2]))

def _trackCheck(connectPass, cursorPass):
	track = pod(connPass=connectPass, curPass=cursorPass)
	for row in track.episodeOwn():
		if os.path.isfile(row[3]):
			track.episodeUpdate('yes', row[1])
		else:
			track.episodeUpdate('No', row[1])	


class sftp_comm:
	
	def __init__(self, connPass=None, curPass=None ,args=None):
		self.connPass = connPass
		self.curPass = curPass
		self.args = args

	def sftpClient(self, host, port=22, username="user", passw=None, keypath=None, keypass=None):
		'''
		sftpClient is vehicle for sftp transfer of podcast files.
		host: Host address of ssh server
		type: string
		port: port number where a connection is to be made. default is 22
		type: interger
		username: user name of the account to connect to. Default is 'user'
		type: string
		passw: password for only password verification ssh servers. (insecure)
		type: string
		keypath: name of private key file. It is connected to the dir /home/<user>/.ssh 
		type: string
		keypass: password for private key
		type: string
		rtype: sftp object
		'''
		try:
			if keypath!=None:
				key=paramiko.RSAKey.from_private_key_file(keypath, password=keypass)
			else:
				pass
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
			else:
				pass	
			if ssh is not None:
				ssh.close()
			else:
				pass	
			
			pass		

	def _auth_(self):
		print('''We are going to connect to your phone
		via ssh/sftp. Are we ready?''')
		
		confirm = input('Y/n: ')
		if confirm.lower() != "y" or 'yes': exit("Goodbye")
		
		if (self.args.host == None):
			print('Some nessary details were omitted.')
			print('usage: python3 podcatch.py [--sshsend or --sshrem] --host "host" --port portnum --user "user" -k "keyname (e.g. id_rsa)"')
			exit('Bye')	
		else:	
			username, host, port = self.args.user, self.args.host, self.args.port

			if not self.args.pkey:	
				print('What\'s the password? Hit enter for private key entry.' )	
				password = input('Password: ')
				print('What\'s the key password? Hit enter if password entry.')
				keypass=input('Keypass: ')		
			else:
				password, keypass = '', self.args.pkey

			key=os.path.join(str(Path.home()), '.ssh', self.args.key)
			sftp_client = self.sftpClient(self.args.host, self.args.port, self.args.user, password, key, keypass)
			return sftp_client
				
	def trackSendAndroid(self):
		'''
		Takes a track and sends it over sftp to your android device.
		Saves it in /sdcard/Music/podcast/<shortname folder>
		connPass: connection pass through
		type: variable
		curPass: cursor pass through
		type: variable
		args: args pass through
		type: variable
		'''
		sftp_client = self._auth_()
		podcast = '/sdcard/Music'
		sftp_client.chdir(podcast)
		sdDir=sftp_client.listdir(podcast)
		pod_folder= os.path.join(podcast, 'podcasts')
		if 'podcasts' not in sdDir: sftp_client.mkdir('podcasts')	
		sftp_client.chdir(pod_folder)	

		current = currentPodcasts(connPass, curPass)

		print('Which numbers would you like to send?')
		print('Seperate selections with spaces.')
		number = intCheckInput()

		podList = sftp_client.listdir(pod_folder)	
		track = pod(connPass=self.connPass, curPass=self.curPass)	
		for en, row in enumerate(track.episodeOwn()):
			series_folder = os.path.join(pod_folder, row[4])
			if row[4] not in podList: sftp_client.mkdir(row[4])
			
			sftp_client.chdir(series_folder)
			if str(en) in number:
				try:
					print('Transfering: {}'.format(row[1]))
					sftp_client.put(row[3], os.path.join(series_folder, row[1]), confirm=True)
					print('Success!')
				except Exception as e:
					print('Err: {1}: {2}'.format(e.__class__, e))
			else:
				print('Error has occured!')		
			sftp_client.chdir(pod_folder)
			sftp_client.close()			

	def trackRemoveAndroid(self):
		'''
		Will look at tracks on phone using subscription database as indicator. 
		Removes tracks specified by user.
		connPass: connection pass through
		type: variable
		curPass: cursor pass through
		type: variable
		args: args pass through
		type: variable
		'''
		sftp_client = self._auth_()
		podcast = '/sdcard/Music' 
		sftp_client.chdir(podcast) #changes to dir above
		sdDir=sftp_client.listdir(podcast) #gets a list of dir in the Music dir
		pod_folder= os.path.join(podcast, 'podcasts')
		if 'podcasts' not in sdDir: #checks if podcasts dir in music
			print('You currently don\'t have podcasts in the default dir.')
			exit('Goodbye') 	
		else:
			pass

		subs = pod(connPass=connPass, curPass=curPass) #instantiates db class.	
		
		for en, row in enumerate(subs.subsRead()): #subs data used to select folder.
			print('[{0}] {1}'. format(str(en), row[1]))
		print('From which series would you like to remove episodes?') 
		print('Please separate selections with spaces')	
		number= intCheckInput() #takes number as input and verifies they are all integers
		
		for en, row in enumerate(subs.subsRead()): #subs data used to select folder and get file listings within each
			folder = os.path.join(pod_folder, row[1])
			if str(en) in number:
				
				if sftp_client.getcwd() != folder: sftp_client.chdir(folder) #switches to folder dir.
		
				fileList = sftp_client.listdir(folder) #gets file listing for specific folder.
			else:
				pass

			for enum, f in enumerate(fileList): #creates a rough number system to list: folder and track.
				print("[{0}-{1}] {2}".format(str(en), str(enum), f))
				sftp_client.chdir(pod_folder)

		print('Which episodes would you like to remove?')
		print('Please use the n-n with a space between (e.g. 1-1 2-2 3-3)')		
		n0 = input("> ")
		n1=n0.split(" ")
		n2 = [n.split('-') for n in n1]  #should be [[1,1],[2,2]] etc.
			
		for n in n2: #similar verification to intCheckInput
			verify(n)
			if not verify: 
				sftp_client.close()
				exit()
			else:
				pass		

		for en, row in enumerate(subs.subsRead()): #accesses folders via subs data
			folder = os.path.join(pod_folder, row[1])#creates folder
			for n in n2:	#iterates through list of lists.
				if str(en) == n[0]: #indicates folder
					if sftp_client.getcwd() != folder: sftp_client.chdir(folder)

					fileList=sftp_client.listdir(folder)
					sftp_client.remove(fileList[n[1]]) #indicates index of file to remove.
				else:
					pass		
		sftp_client.close()
		
def _first_run():
	dbfile = os.path.join(str(Path.home()),'.dbpath')
	
	if platform.os.name == 'posix':
		
		if os.path.isfile('podcatch.py') and not os.path.isfile(dbfile): 
			db = os.path.join(os.getcwd(), 'podbase.db')
			with open(dbfile, 'w+') as dbpath:
				dbpath.write(db)
			
			if platform.system() == "Linux":
				bash_aliases = os.path.join(str(Path.home()),'.bash_aliases')
			else:
				bash_aliases= os.path.join(str(Path.home()), '.bash_profile')			

			if os.path.isfile(bash_aliases):	
				dbpod = ww(title=bash_aliases, text='alias pod="python3 {}/podcatch.py"'.format(os.getcwd()))
				dbpod.txtWriter(mode='a')
				exit()			
			else:
				dbpod = ww(title=bash_aliases, text='alias pod="python3 {}/podcatch.py"'.format(os.getcwd()))
				dbpod.txtWriter(mode='w+')
				exit()	

		else:
			with open(dbfile, 'r') as dbpath:
				for line in dbpath:
					database = line				
			return database
	else:
		print('You are not on a posix system.')
		exit()		

def _database_conn_cur(path):
	conn = sqlite3.connect(path)
	c = conn.cursor()
	tables=pod(connPass=conn, curPass=c)
	tables.subsTable()
	tables.episodeTable()
	_trackCheck(conn, c)
	return conn, c

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-f', dest='feed', help="Adds a new feed to the subscription list. Must be used with --name. -v is optional use. ")
	parser.add_argument('--name', dest='name', help='Identifies feed subscription by name you gave when subscribing. Names must be in quotation marks.')
	parser.add_argument('-r', dest='rfeed', help='Removes a feed from the subscription list. Must be in quotation marks.', action="store_true")
	parser.add_argument('--update', dest ='update', help='Checks for new updates. Can be used with -v', action='store_true')
	parser.add_argument('--view', dest='view', help='Displays current subscriptions.', action='store_true')
	parser.add_argument('-v', dest="verbose", action="store_true", help="Displays more information about what the database is doing.")
	parser.add_argument('--recent', dest='recent', help='Gets the most recent episode.', action='store_true')
	parser.add_argument('--load', dest='load', action='store_true', help='Loads urls of feeds into database from subs.txt file.')
	parser.add_argument('--series', dest='series', action='store_true', help='Displays all episodes of the series. Can be used with --name.')
	parser.add_argument('--delete', dest='delete', action='store_true', help='Remove files from podcast collection.')
	parser.add_argument('--current', dest='current', action='store_true', help='Shows which files you currently have downloaded.')
	parser.add_argument('--remove', dest='remove', action='store_true', help='Removes complete series from hard drive and database. Use with caution. Must be used with --name.')
	parser.add_argument('--sshsend', dest='send', action='store_true', help='Sends track to an ssh enabled device.')
	parser.add_argument('--host', dest='host', help='Host name for ssh server. Required with --ssh flag.')
	parser.add_argument('--port', dest='port', help='Port number for ssh server. Default is 22 if undeclared.', default=22)
	parser.add_argument('--user', dest='user', help='Username for ssh server. Default is user if undeclared.', default='user')
	parser.add_argument('--pkey', dest="pkey", help='Password for key encryption. If undeclared, it will be asked before connection.')
	parser.add_argument('-k', dest='key', default=None, help='Name of private key for passwordless access. Must be located in the .ssh dir of the home folder.')
	parser.add_argument('--sshrem', dest='rem', help='Removes user specified tracks from ssh android device.')
	parser.add_argument('--version', dest='version', help='Gives current version.', action='store_true')
	args = parser.parse_args()
	
	database = _first_run()
	conn, c = _database_conn_cur(database)
	version = 'version: 0.9.3'

	dl = Downloading(connP=conn, curP=c, args=args)
	subs = Subscriptions(connectP=conn, cursorP=c, args=args)


	if args.feed or args.rfeed or args.view:	
		subs.subscriptionUpdater()

	if args.update or args.recent or args.series:
		
		try:
			dataBasePopulate(conn, c, args)
		
		except Exception as e:
			print("Err: {0}: {1}".format(e.__class__, str(e)))

		if args.update:
			print("Would you like to see recent episodes?")
			rec = input("Y/n")
			if rec.lower() == 'y':
				dl.recentEpsDL()
			else:
				exit()
		elif args.recent: 
			dl.recentEpsDL()
		elif args.series: 
			dl.seriesDownload()			

	if args.load: subs.subLoad()
	if args.delete: dl.deleteTrack()			
	if args.current: currentPodcasts(conn, c)
	if args.remove: subs.removeSeries()
	if args.send or args.rem: 
		sftp_c = sftp_comm(conn, c, args)
		if args.send: sftp_c.trackSendAndroid()
		if args.rem: sftp_c.trackRemoveAndroid()
	else:
		pass

	if args.version and platform.os.name == 'posix': 
		print(version)
		exit()
	else:
		pass

	c.close()
	conn.close()

if __name__ == "__main__":
	main()
		