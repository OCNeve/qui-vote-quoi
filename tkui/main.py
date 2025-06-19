from customtkinter import CTk, CTkFrame, CTkLabel, CTkCheckBox, CTkComboBox, CTkEntry, CTkButton, CTkScrollableFrame
from tkinter import StringVar, messagebox
from stats_work.main import get_vote
from utils.pgconnector import PGConnection
import os
import subprocess
import sys

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')

pgc = PGConnection(dotenv_path)
pgc.connect_to_db()

class Root(CTk):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.title("Qui vote quoi")
		self.geometry("600x500")  # Agrandir la fenêtre
		main_frame = MainFrame(master=self)
		main_frame.pack(pady=5, padx=5, fill="both", expand=True)

class MainFrame(CTkFrame):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.selected_lower_date = StringVar(self) 
		self.selected_upper_date = StringVar(self)
		self.name_entry = CTkEntry 
		self.result_frame = ResultFrame(self)
		self.make_widgets()

	def make_widgets(self):
		# Titre principal
		title_label = CTkLabel(master=self, text="🗳️ Qui Vote Quoi", 
		                      font=("Ubuntu", 20, 'bold'))
		title_label.pack(pady=10, padx=5)
		
		# Frame pour les boutons principaux
		buttons_frame = CTkFrame(self)
		buttons_frame.pack(pady=10, padx=5, fill="x")
		
		# Bouton Dashboard
		dashboard_button = CTkButton(master=buttons_frame, 
		                           text="📊 Ouvrir Dashboard", 
		                           command=self.open_dashboard,
		                           fg_color="#e74c3c",
		                           hover_color="#c0392b",
		                           font=("Ubuntu", 14, 'bold'))
		dashboard_button.pack(pady=5, padx=10, side="top", fill="x")
		
		# Séparateur
		separator = CTkLabel(master=self, text="─" * 50, 
		                    font=("Ubuntu", 12))
		separator.pack(pady=5)
		
		# Section recherche classique
		search_label = CTkLabel(master=self, text="Recherche Rapide", 
		                       font=("Ubuntu", 16, 'bold'))
		search_label.pack(pady=(10, 5), padx=5)
		
		label = PrettyLabel(master=self, text="Entrez un prénom:")
		label.pack(pady=5, padx=5)
		
		self.name_entry = CTkEntry(master=self, placeholder_text="Ex: MARIE, JEAN...")
		self.name_entry.pack(pady=5, padx=5)
		
		# Frame pour les dates
		date_frame = CTkFrame(self)
		date_frame.pack(pady=5, padx=5)
		
		date_label = CTkLabel(master=date_frame, text="Tranche d'âge (années de naissance):")
		date_label.pack(pady=5)
		
		lower_date_options = list(map(str, range(1910, 2023)))
		upper_date_options = list(map(str, range(1910, 2023)))
		self.selected_lower_date.set(lower_date_options[len(lower_date_options)//2]) 
		self.selected_upper_date.set(upper_date_options[-1]) 
		
		dates_container = CTkFrame(date_frame)
		dates_container.pack(pady=5)
		
		lower_date_choice = CTkComboBox(master=dates_container, 
		                               variable=self.selected_lower_date, 
		                               values=lower_date_options, 
		                               width=100)
		upper_date_choice = CTkComboBox(master=dates_container, 
		                               variable=self.selected_upper_date, 
		                               values=upper_date_options, 
		                               width=100)
		
		lower_date_choice.grid(pady=5, padx=5, column=0, row=0)
		CTkLabel(master=dates_container, text="à").grid(column=1, row=0, padx=5)
		upper_date_choice.grid(pady=5, padx=5, column=2, row=0)
		
		# Bouton recherche
		search_button = CTkButton(master=self, text="🔍 Rechercher", 
		                         command=self.get_params,
		                         font=("Ubuntu", 12, 'bold'))
		search_button.pack(pady=10, padx=5)

	def open_dashboard(self):
		"""Ouvrir le dashboard Streamlit"""
		try:
			# Vérifier si streamlit est installé
			try:
				import streamlit
			except ImportError:
				response = messagebox.askyesno(
					"Streamlit non installé", 
					"Streamlit n'est pas installé. Voulez-vous l'installer maintenant?\n\n"
					"Cette opération peut prendre quelques minutes."
				)
				if response:
					self.install_streamlit_dependencies()
				return
			
			# Chemin vers le fichier dashboard
			dashboard_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
			                             'dashboard', 'main.py')
			
			# Créer le dossier dashboard s'il n'existe pas
			dashboard_dir = os.path.dirname(dashboard_path)
			if not os.path.exists(dashboard_dir):
				os.makedirs(dashboard_dir)
				
			# Créer le fichier dashboard s'il n'existe pas
			if not os.path.exists(dashboard_path):
				self.create_dashboard_file(dashboard_path)
			
			# Lancer Streamlit
			messagebox.showinfo("Dashboard", 
			                   "Le dashboard va s'ouvrir dans votre navigateur.\n"
			                   "Fermer cette fenêtre n'arrêtera pas le dashboard.")
			
			subprocess.Popen([sys.executable, "-m", "streamlit", "run", dashboard_path])
			
		except Exception as e:
			messagebox.showerror("Erreur", f"Impossible d'ouvrir le dashboard:\n{str(e)}")

	def install_streamlit_dependencies(self):
		"""Installer les dépendances Streamlit"""
		try:
			# Afficher un message d'installation
			install_window = CTk()
			install_window.title("Installation en cours...")
			install_window.geometry("400x200")
			
			install_label = CTkLabel(install_window, 
			                        text="Installation des dépendances en cours...\n"
			                             "Veuillez patienter...",
			                        font=("Ubuntu", 14))
			install_label.pack(expand=True)
			
			install_window.update()
			
			# Installer les packages
			packages = ["streamlit", "streamlit-folium", "folium", "pandas", "requests"]
			for package in packages:
				subprocess.check_call([sys.executable, "-m", "pip", "install", package])
			
			install_window.destroy()
			messagebox.showinfo("Installation terminée", 
			                   "Les dépendances ont été installées avec succès!")
			
		except Exception as e:
			messagebox.showerror("Erreur d'installation", 
			                   f"Erreur lors de l'installation:\n{str(e)}")

	def create_dashboard_file(self, path):
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

if __name__ == "__main__":
    main()
'''
		
		# Créer le fichier
		with open(path, 'w', encoding='utf-8') as f:
			f.write(dashboard_code)

	def get_params(self):
		self.result_frame.pack_forget()
		del self.result_frame
		self.result_frame = ResultFrame(self)
		try:
			results = get_vote(pgc, self.name_entry.get().upper(), 
			                  (self.selected_lower_date.get(), self.selected_upper_date.get()))
			self.result_frame.add_result(results)
			self.result_frame.pack(pady=10, padx=5, fill="both", expand=True)
		except Exception as e:
			messagebox.showerror("Erreur", f"Erreur lors de la recherche:\n{str(e)}")

class PrettyLabel(CTkLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, font=("Ubuntu", 12, 'bold'), **kwargs)

class ResultFrame(CTkScrollableFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, height=200, width=300, **kwargs)
       
    def add_result(self, result_set):
    	if not result_set:
    		no_result_label = PrettyLabel(self, text="Aucun résultat trouvé")
    		no_result_label.pack(pady=10)
    		return
    	
    	title_label = PrettyLabel(self, text="Top 5 des candidats:")
    	title_label.pack(pady=5)
    	
    	labels = []
    	for i, result in enumerate(result_set):
    		vote_text = f"{i+1}. {result[1]} {result[0]} - {result[2]:,} votes"
    		labels.append(CTkLabel(self, text=vote_text, font=("Ubuntu", 11)))

    	list(map(lambda x: x.pack(pady=2, anchor="w"), labels))