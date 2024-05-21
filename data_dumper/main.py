from time import time
st = time()


from pgconnector import PGConnection
import os
import requests
import zipfile
from psycopg2.extras import execute_batch
import csv


def downlaod_and_extract():
	def download_file(url, filename=''):
		try:
			if filename:
			    pass            
			else:
			    filename = req.url[downloadUrl.rfind('/')+1:]

			with requests.get(url) as req:
				with open(filename, 'wb') as f:
					for chunk in req.iter_content(chunk_size=8192):
						if chunk:
							f.write(chunk)
				return filename
		except Exception as e:
		    print(e)
		    return None


	def extract_files(archive_name, output_dir):
		with zipfile.ZipFile(archive_name, 'r') as zip:
			zip.extractall(output_dir)


	downloadLink = 'https://www.insee.fr/fr/statistiques/fichier/2540004/dpt2021_csv.zip'

	archive = download_file(downloadLink, './names.csv.zip')

	extract_files(archive, "./data")

downlaod_and_extract()

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')

pgc = PGConnection(dotenv_path)
pgc.connect_to_db()

data = []
with open('./data/dpt2021.csv', mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file, delimiter=';')
    for row in reader:
        data.append(row)


departements = set(row['dpt'] for row in data)
execute_batch(pgc.cursor, 
"""
INSERT INTO voters.departements (numero) 
VALUES (%s);
""",
[(dpt,) for dpt in departements])
print('inserted departements')

years = set(row['annais'] for row in data)
execute_batch(pgc.cursor, 
"""
INSERT INTO voters.annees (valeur) 
VALUES (%s);
""",
[(year,) for year in years])
print('inserted années')

prenoms = set(row['preusuel'] for row in data)
execute_batch(pgc.cursor, 
"""
INSERT INTO voters.prenoms (valeur) 
VALUES (%s);
""",
[(prenom,) for prenom in prenoms])
print('inserted prenoms')



# Fetch departement ids
pgc.cursor.execute("SELECT id, numero FROM voters.departements;")
dept_ids = {row[1]: row[0] for row in pgc.cursor.fetchall()}

# Fetch year ids
pgc.cursor.execute("SELECT id, valeur FROM voters.annees;")
year_ids = {row[1]: row[0] for row in pgc.cursor.fetchall()}

# Fetch prenoms ids
pgc.cursor.execute("SELECT id, valeur FROM voters.prenoms;")
prenom_ids = {row[1]: row[0] for row in pgc.cursor.fetchall()}

# Prepare data for insertion into prenoms table
prenoms_data = [
    (dept_ids[row['dpt']], year_ids[row['annais']], prenom_ids[row['preusuel']], row['nombre'])
    for row in data
]

# Insert data into prenoms table
execute_batch(pgc.cursor, 
"""
INSERT INTO voters.prenoms_occurences (departement_id, annee_id, prenom_id, compte) 
VALUES (%s, %s, %s, %s) 
ON CONFLICT (departement_id, annee_id) DO NOTHING;
""", 
prenoms_data)
print('inserted prenoms occurences')

pgc.connection.commit()
pgc.close()

print(time()-st	)