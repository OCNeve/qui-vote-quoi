from time import time
st = time()


from pgconnector import PGConnection
import os
from psycopg2.extras import execute_batch
import numpy as np
from psycopg2.extensions import register_adapter, AsIs
import csv
import pandas as pd
from file_manager import FileManager

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')

pgc = PGConnection(dotenv_path)
pgc.connect_to_db()

register_adapter(np.int64, AsIs)

def extract_names_data():
	fm = FileManager(url='https://www.insee.fr/fr/statistiques/fichier/2540004/dpt2021_csv.zip', name='./names.csv.zip', path = './data')
	fm.download_and_extract()
	data = []
	with open('./data/dpt2021.csv', mode='r', encoding='utf-8') as file:
	    reader = csv.DictReader(file, delimiter=';')
	    for row in reader:
	        data.append(row)
	return data


def extract_elections_data():
	fm = FileManager(url='https://www.data.gouv.fr/fr/datasets/r/98eb9dab-f328-4dee-ac08-ac17211357a8', name='./elections.xlsx', path = './data')
	fm.download_file()
	return pd.read_excel('./data/elections.xlsx')

def import_names_data(data):
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
	ON CONFLICT (departement_id, annee_id, prenom_id) DO NOTHING;
	""", 
	prenoms_data)
	print('inserted prenoms occurences')


data = extract_names_data()
import_names_data(data)



df = extract_elections_data()
nom_column_index = df.columns.get_loc("N°Panneau")
candidate_columns = [col for i,col in enumerate(df.columns) if i>=nom_column_index]
n = 7
candidate_columns = [candidate_columns[i:i+n] for i in range(0, len(candidate_columns), n)]
candidates_names = set()
first_row = df.iloc[0]

for i in candidate_columns:
	candidates_names.add((first_row[i[2]], first_row[i[3]]))

execute_batch(pgc.cursor, """
INSERT INTO voters.candidats (nom, prenom)
VALUES (%s, %s);
""", list(candidates_names))
print('inserted candidat names')

pgc.cursor.execute("SELECT id, nom, prenom FROM voters.candidats;")
candidate_ids = {(row[1], row[2]): row[0] for row in pgc.cursor.fetchall()}

# Insert department names where they are missing
departements = df[['Code du département', 'Libellé du département']].drop_duplicates()

execute_batch(pgc.cursor, """
UPDATE voters.departements
SET nom = %s
WHERE numero = %s AND (nom IS NULL OR nom = '');
""", [(row['Libellé du département'], row['Code du département']) for _, row in departements.iterrows()])
print('updated departements with their names')

# Fetch department ids
pgc.cursor.execute("SELECT id, numero FROM voters.departements;")
department_ids = {row[1]: row[0] for row in pgc.cursor.fetchall()}

# Prepare the data for votes_par_departements
votes_data = []

for code_departement, group in df.groupby('Code du département'):
	try:
		department_id = department_ids[code_departement]
	except KeyError:
		print(f'Unknown departement with code {code_departement}')
	total_inscrits = group['Inscrits'].sum()

	for i in candidate_columns:
	    nom = group.iloc[0][i[2]]
	    prenom = group.iloc[0][i[3]]
	    candidat_id = candidate_ids[(nom, prenom)]
	    total_voix = group[i[5]].sum()  # Column index 5 is assumed to be 'Voix' for the candidate

	    votes_data.append((candidat_id, department_id, total_voix, total_inscrits))

# Insert the summarized votes data into the database
execute_batch(pgc.cursor, """
INSERT INTO voters.votes_par_departements (candidat_fk, departement_id, compte_votes, compte_inscrit)
VALUES (%s, %s, %s, %s);
""", votes_data)

print('inserted votes_par_departements')


pgc.connection.commit()


pgc.close()

print(time()-st	)