import requests
import zipfile
import os

class FileManager:
	def __init__(self, url=None, name=None, path=None):
		self.url = url
		self.name = name
		self.path = path


	def download_file(self):
		try:
			if self.name:
			    pass            
			else:
			    self.name = req.url[downloadUrl.rfind('/')+1:]

			with requests.get(self.url) as req:
				with open(os.path.join(self.path, self.name), 'wb') as f:
					for chunk in req.iter_content(chunk_size=8192):
						if chunk:
							f.write(chunk)
				return self.name
		except Exception as e:
		    print(e)
		    return None


	def extract_files(self, archive_name, output_dir):
		with zipfile.ZipFile(os.path.join(output_dir, archive_name), 'r') as zip:
			zip.extractall(output_dir)
		os.remove(os.path.join(output_dir, archive_name))

	def download_and_extract(self):
		archive = self.download_file()
		self.extract_files(archive, self.path)