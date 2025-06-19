import sys
import time
import subprocess
import os

def remake_database():
	if input('Are you sure you want to import?\nTHIS WILL DROP AND REMAKE THE CURRENT DATABASE!\n\t\t[y/n]').lower() == 'y':
		import subprocess
		subprocess.run(["docker", "compose", "down"])
		time.sleep(1)
		subprocess.run(["docker", "volume", "rm", "vote_par_prenom_postgres"])
		time.sleep(1)
		subprocess.run(["docker", "compose", "up", "-d"])
		time.sleep(5)
		return
	sys.exit()

def start_dashboard():
	"""Lancer le dashboard Streamlit"""
	try:
		# Vérifier si streamlit est installé
		try:
			import streamlit
		except ImportError:
			print("Streamlit n'est pas installé. Installation en cours...")
			subprocess.check_call([sys.executable, "-m", "pip", "install", 
			                      "streamlit", "streamlit-folium", "folium", "pandas", "requests"])
			print("Installation terminée!")
		
		# Créer le dossier dashboard s'il n'existe pas
		dashboard_dir = os.path.join(os.path.dirname(__file__), 'dashboard')
		if not os.path.exists(dashboard_dir):
			os.makedirs(dashboard_dir)
		
		# Chemin vers le fichier dashboard
		dashboard_path = os.path.join(dashboard_dir, 'main.py')
		
		# Créer le fichier dashboard s'il n'existe pas
		if not os.path.exists(dashboard_path):
			create_dashboard_file(dashboard_path)
		
		print("Démarrage du dashboard Streamlit...")
		print("Le dashboard s'ouvrira dans votre navigateur à l'adresse: http://localhost:8501")
		print("Appuyez sur Ctrl+C pour arrêter le serveur")
		
		# Lancer Streamlit
		subprocess.run([sys.executable, "-m", "streamlit", "run", dashboard_path])
		
	except Exception as e:
		print(f"Erreur lors du lancement du dashboard: {e}")

def create_dashboard_file(path):
	"""Créer le fichier dashboard.py"""
	dashboard_code = '''import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import requests
import sys
import os

# Ajouter le répertoire parent au path pour pouvoir importer nos modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from stats_work.main import get_vote, get_name_to_dept
from utils.pgconnector import PGConnection
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Qui Vote Quoi - Dashboard", layout="wide")

# Connexion à la base de données
@st.cache_resource
def init_db_connection():
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    pgc = PGConnection(dotenv_path)
    pgc.connect_to_db()
    return pgc

# Chargement des données géographiques des départements français
@st.cache_data
def load_france_geojson():
    url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements.geojson"
    try:
        response = requests.get(url)
        return response.json()
    except:
        return None

def create_france_map(highlighted_dept=None):
    france_center = [46.603354, 1.888334]
    m = folium.Map(location=france_center, zoom_start=6, tiles='OpenStreetMap')
    
    geojson_data = load_france_geojson()
    
    if geojson_data:
        def style_function(feature):
            dept_code = feature['properties']['code']
            if highlighted_dept and dept_code == highlighted_dept:
                return {'fillColor': 'red', 'color': 'darkred', 'weight': 3, 'fillOpacity': 0.8}
            else:
                return {'fillColor': 'lightblue', 'color': 'blue', 'weight': 1, 'fillOpacity': 0.3}
        
        folium.GeoJson(geojson_data, style_function=style_function,
                      tooltip=folium.features.GeoJsonTooltip(fields=['nom', 'code'], 
                                                           aliases=['Département:', 'Code:'])).add_to(m)
    return m

def main():
    st.title("🗳️ Qui Vote Quoi - Dashboard Interactif")
    st.markdown("---")
    
    pgc = init_db_connection()
    
    st.sidebar.header("Paramètres de recherche")
    prenom = st.sidebar.text_input("Entrez un prénom:", placeholder="Ex: MARIE, JEAN...")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        annee_debut = st.selectbox("Année début:", options=list(range(1910, 2023)), 
                                  index=len(list(range(1910, 2023)))//2)
    with col2:
        annee_fin = st.selectbox("Année fin:", options=list(range(1910, 2023)), 
                                index=len(list(range(1910, 2023)))-1)
    
    rechercher = st.sidebar.button("🔍 Analyser", type="primary")
    
    col_map, col_results = st.columns([2, 1])
    
    with col_map:
        st.subheader("Carte de France Interactive")
        
        if rechercher and prenom:
            try:
                dept_info = get_name_to_dept(pgc, prenom.upper(), (str(annee_debut), str(annee_fin)))
                if dept_info:
                    carte = create_france_map(highlighted_dept=dept_info)
                    st_folium(carte, width=700, height=500)
                    st.success(f"Le prénom '{prenom.upper()}' est le plus représenté dans le département: **{dept_info}**")
                else:
                    carte = create_france_map()
                    st_folium(carte, width=700, height=500)
                    st.warning("Aucun département trouvé pour ce prénom dans cette tranche d'âge.")
            except Exception as e:
                carte = create_france_map()
                st_folium(carte, width=700, height=500)
                st.error(f"Erreur lors de la recherche: {str(e)}")
        else:
            carte = create_france_map()
            st_folium(carte, width=700, height=500)
            st.info("Entrez un prénom et cliquez sur 'Analyser' pour voir le département correspondant s'illuminer.")
    
    with col_results:
        st.subheader("Résultats de l'analyse")
        
        if rechercher and prenom:
            try:
                resultats_vote = get_vote(pgc, prenom.upper(), (str(annee_debut), str(annee_fin)))
                if resultats_vote:
                    st.write("**Top 5 des candidats dans ce département:**")
                    df_results = pd.DataFrame(resultats_vote, columns=['Nom', 'Prénom', 'Votes'])
                    st.dataframe(df_results, use_container_width=True)
                    st.bar_chart(df_results.set_index('Nom')['Votes'])
                else:
                    st.warning("Aucun résultat de vote trouvé.")
            except Exception as e:
                st.error(f"Erreur lors de la récupération des votes: {str(e)}")
        else:
            st.info("Les résultats d'analyse apparaîtront ici après la recherche.")
    
    st.markdown("---")
    st.markdown("""
    ### Comment ça marche ?
    1. **Entrez un prénom** dans la barre latérale
    2. **Sélectionnez une tranche d'âge** (années de naissance)
    3. **Cliquez sur Analyser** pour voir :
       - Le département où ce prénom est le plus représenté (en rouge sur la carte)
       - Les tendances de vote de ce département
    
    *Les données proviennent de l'INSEE (prénoms) et du gouvernement français (élections).*
    """)

if __name__ == "__main__":
    main()
'''
	
	# Créer le fichier
	with open(path, 'w', encoding='utf-8') as f:
		f.write(dashboard_code)


if len(sys.argv) == 1:
	print('Argument required. Use help to list arguments.')
else:
	if sys.argv[1] == "import":
		print('importing data')
		from data_dumper.main import _import
		if not (len(sys.argv) == 3 and sys.argv[2] == "-y"):
			remake_database()
		_import()
	elif sys.argv[1] == "desktopui":
		from tkui.main import Root
		root = Root()
		root.mainloop()
	elif sys.argv[1] == "dashboard":
		start_dashboard()
	elif sys.argv[1] == "webserver":
		print('starting webserver')
	elif sys.argv[1] == "cli":
		print('starting cli')
	else:
		print("Possible arguments are as follows:")
		print("\timport:   \timport and dump data into the database")
		print("\tdesktopui:\tstartup a tkinter GUI")
		print("\tdashboard:\tstartup a Streamlit dashboard")
		print("\twebserver:\tstartup a webserver to server apis")
		print("\tcli:      \tstartup a cli")