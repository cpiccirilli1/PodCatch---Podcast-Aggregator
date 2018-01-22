
import pymtp as mtp

class podTrack:

	def __init__(self, device):
		self.device = device

	def sendTrack(self):
		pass

	def deleteTrack(self):
		pass

	def deviceMusicFolders(self):
		folder = [f.folder_id for f in self.device.get_parent_folders() if f.name == "Music"]
		folderSet = set(folder)
		allFolders = self.device.get_folder_list()
		newLength = None
		current= len(folderSet)
		while current !=  newLength:
			current = len(folderSet)

			for k in allFolders:
				f = allFolders[k]
				if f.parent_id in folderSet:
					f.append(folderSet)

			newLength = len(folderSet)		
		return folderSet	

	def computerMusicFolders(self):
		pass

