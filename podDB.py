#!/usr/bin/python3
'''
v0.0.1
Custom module for database management and executions in sqlite3. 
Importing sqlite3 isn't currently necessary but may become so in the future.
'''
#import sqlite3 as lite

class podData:
	def __init__(self, series=None, src=None, title=None, hdpath=None, connPass=None, curPass=None, date=None, published=None, shortname=None, downloaded='No'):
		self.series = series #Title of the Series
		self.ep_src = src #episode url
		self.sub_src = src #RSS Feed URL
		self.title = title #Title of the episode
		self.hdpath = hdpath #Where it's stored
		self.date=date #date of download/DB upload.
		self.published = published #When episode was posted to the www. 
		self.curPass=curPass #passes through current cursor
		self.connPass = connPass #passes through current connection
		self.shortname = shortname #gathered from the args.name, used as an easy identifier for users
		self.downloaded = downloaded #self explanatory.
	def episodeTable(self):
		'''
		creates table for episodes: Time it was added, time published, series name, MP3 url,
		title of the episode, and where it is stored.
		'''
		self.curPass.execute("CREATE TABLE IF NOT EXISTS episode(datestamp TEXT, created TEXT UNIQUE,series TEXT, mp3url TEXT, title TEXT, mp3path TEXT, shortname TEXT, downloaded TEXT)")

	def episodeAdd(self):
		self.curPass.execute('INSERT OR IGNORE INTO episode(datestamp, created, series, title, mp3url, mp3path, shortname, downloaded) VALUES(?, ?, ?, ?, ?, ?, ?, ?)',
			(self.date, self.published, self.series, self.title, self.ep_src, self.hdpath, self.shortname, self.downloaded))
		self.connPass.commit()

	def episodeUpdate(self, dl, name):
		self.curPass.execute('UPDATE episode SET downloaded=? WHERE title=?', (dl, name,))
		self.connPass.commit()


	def episodeRecent(self):
		self.curPass.execute('SELECT series, title, mp3url, mp3path, created, shortname, downloaded FROM episode ORDER BY created DESC LIMIT 10')
		data = self.curPass.fetchall()
		return data	

	def episodeOwn(self):
		self.curPass.execute('SELECT series, title, created, mp3path, shortname, downloaded FROM episode WHERE downloaded="yes" ORDER BY created DESC')
		data = self.curPass.fetchall()
		return data		

	def seriesDownload(self, shortname):
		self.curPass.execute('SELECT series, title, mp3url, mp3path, created, shortname downloaded FROM episode WHERE shortname=?  ORDER BY created', (shortname,))		
		data=self.curPass.fetchall()
		return data

	def subsTable(self):
		self.curPass.execute("CREATE TABLE IF NOT EXISTS subscriptions(datestamp TEXT, series TEXT UNIQUE, subsrc TEXT)")

	def subsAdd(self):
		self.curPass.execute("INSERT OR IGNORE INTO subscriptions(datestamp, series, subsrc) VALUES(?, ?, ?)",
			(self.date, self.series, self.sub_src))
		self.connPass.commit()

	def subsRead(self):
		self.curPass.execute('SELECT * FROM subscriptions')
		data = self.curPass.fetchall()
		return data	

	def subsDelete(self, name):
		self.curPass.execute('DELETE FROM subscriptions WHERE series=?', (name,))
		self.connPass.commit()