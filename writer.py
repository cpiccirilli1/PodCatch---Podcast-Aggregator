'''
version 1.0.2
'''

import requests, sys

class Writer:

	def __init__(self, title=None, src=None, bit = 1024, text = None):
		self.title = title
		self.src = src
		self.bit = bit
		self.text = text

	def fileWriter(self):
		title = isstring(s)
		if (self.title == None) | (self.src == None):
			print('This requires both a TITLE and SOURCE.')
			return
		elif not title:
			print('Title Must Be A String!')
			return
		else:	
			req = requests.get(self.src)

			with open(self.title, 'wb') as f:

				for chunk in req.iter_content(self.bit):
					f.write(chunk) 
			return		
					
	def txtWriter(self):
		file = isstring(self.title)
		text = isstring(self.text)
		if not file:
			print('File Name is not a String.')
			return
		elif not text:
			print('Text is not a string.')
			return
		else:	
			with open(self.title, 'w') as fn:
				fn.write('\n'+self.text)

def isstring(s):
    # if we use Python 3
    if (sys.version_info[0] >= 3):
        return isinstance(s, str)
    # we use Python 2
    return isinstance(s, basestring)