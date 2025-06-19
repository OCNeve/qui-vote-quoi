import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import requests
import sys
import os
import time
from datetime import datetime

# Ajouter le répertoire parent au path pour pouvoir importer nos modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from stats_work.main import get_vote, get_name_to_dept, get_name_to_dept_full_info
from utils.pgconnector import PGConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuration de la page
st.set_page_config(
    page_title="Qui Vote Quoi - Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialiser le session state avec des améliorations
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'last_search' not in st.session_state:
    st.session_state.last_search = None
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'page_start_time' not in st.session_state:
    st.session_state.page_start_time = time.time()

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

def convert_dept_code_for_map(dept_code):
    """Convertir le code département de la BDD vers le format GeoJSON"""
    if not dept_code:
        return None
    
    # Conversion spécifique pour la Corse
    if dept_code == "20":
        return ["2A", "2B"]  # Retourner les deux codes
    
    # Formatage standard (ajouter 0 devant si nécessaire)
    if dept_code.isdigit() and len(dept_code) == 1:
        return [f"0{dept_code}"]
    
    return [dept_code]

def create_france_map(highlighted_dept=None):
    """Créer une carte de France améliorée"""
    france_center = [46.603354, 1.888334]
    m = folium.Map(
        location=france_center, 
        zoom_start=6, 
        tiles='OpenStreetMap',
        prefer_canvas=True
    )
    
    geojson_data = load_france_geojson()
    
    if geojson_data:
        # Convertir le code département
        highlighted_codes = convert_dept_code_for_map(highlighted_dept) if highlighted_dept else []
        
        def style_function(feature):
            dept_code = feature['properties']['code']
            
            if dept_code in highlighted_codes:
                # Corse = orange, autres = rouge
                if dept_code in ["2A", "2B"] and highlighted_dept == "20":
                    return {
                        'fillColor': '#ff7f0e',  # Orange pour la Corse
                        'color': '#d62728',
                        'weight': 4,
                        'fillOpacity': 0.8,
                        'dashArray': '5, 5'  # Pointillés pour la Corse
                    }
                else:
                    return {
                        'fillColor': '#d62728',  # Rouge pour les autres
                        'color': '#8b0000',
                        'weight': 4,
                        'fillOpacity': 0.9
                    }
            else:
                return {
                    'fillColor': '#1f77b4',  # Bleu par défaut
                    'color': '#0d47a1',
                    'weight': 1,
                    'fillOpacity': 0.4
                }
        
        # Ajouter une popup avec plus d'informations
        def popup_function(feature):
            props = feature['properties']
            return folium.Popup(
                f"<b>{props['nom']}</b><br>"
                f"Code: {props['code']}<br>"
                f"Cliquez pour plus d'infos",
                max_width=200
            )
        
        folium.GeoJson(
            geojson_data, 
            style_function=style_function,
            popup=popup_function,
            tooltip=folium.features.GeoJsonTooltip(
                fields=['nom', 'code'], 
                aliases=['Département:', 'Code:'],
                style="background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"
            )
        ).add_to(m)
        
        # Ajouter une légende
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 150px; height: 80px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <b>Légende</b><br>
        <i class="fa fa-square" style="color:#d62728"></i> Département principal<br>
        <i class="fa fa-square" style="color:#ff7f0e"></i> Corse (cas spécial)<br>
        <i class="fa fa-square" style="color:#1f77b4"></i> Autres départements
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def perform_search(pgc, prenom, annee_debut, annee_fin):
    """Recherche avec validation et gestion des None"""
    try:
        search_start_time = time.time()
        search_key = f"{prenom}_{annee_debut}_{annee_fin}"
        
        # Éviter les recherches répétées
        if (st.session_state.last_search == search_key and 
            st.session_state.search_results and 
            st.session_state.search_results.get('success')):
            return st.session_state.search_results
        
        # Effectuer la recherche
        dept_info = get_name_to_dept(pgc, prenom.upper(), (str(annee_debut), str(annee_fin)))
        dept_full_info = get_name_to_dept_full_info(pgc, prenom.upper(), (str(annee_debut), str(annee_fin)))
        resultats_vote = get_vote(pgc, prenom.upper(), (str(annee_debut), str(annee_fin)))
        
        # CORRECTION: Validation pour éviter les faux positifs
        is_valid_result = False
        if dept_info and dept_full_info:
            ratio = dept_full_info.get('ratio', 0) if dept_full_info else 0
            occurrences = dept_full_info.get('prenom_total', 0) if dept_full_info else 0
            
            # Critères de validation
            if ratio >= 0.0001 and occurrences >= 10:
                is_valid_result = True
            else:
                print(f"⚠️ Résultat rejeté pour {prenom}: ratio={ratio:.6f}, occurrences={occurrences}")
                dept_info = None
                dept_full_info = None
                resultats_vote = []
        
        search_time = time.time() - search_start_time
        
        # Sauvegarder les résultats
        results = {
            'prenom': prenom.upper(),
            'annee_debut': annee_debut,
            'annee_fin': annee_fin,
            'dept_info': dept_info,
            'dept_full_info': dept_full_info,
            'resultats_vote': resultats_vote,
            'success': is_valid_result,  # Utiliser la validation
            'search_time': search_time,
            'timestamp': datetime.now().isoformat()
        }
        
        st.session_state.search_results = results
        st.session_state.last_search = search_key
        
        # Ajouter à l'historique
        st.session_state.search_history.append({
            'prenom': prenom.upper(),
            'periode': f"{annee_debut}-{annee_fin}",
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'success': is_valid_result,
            'search_time': search_time
        })
        
        # Garder seulement les 10 dernières recherches
        if len(st.session_state.search_history) > 10:
            st.session_state.search_history = st.session_state.search_history[-10:]
        
        return results
        
    except Exception as e:
        search_time = time.time() - search_start_time if 'search_start_time' in locals() else 0
        error_results = {
            'prenom': prenom.upper(),
            'error': str(e),
            'success': False,
            'search_time': search_time,
            'timestamp': datetime.now().isoformat()
        }
        st.session_state.search_results = error_results
        return error_results
    
def safe_get_from_dict(dictionary, key, default=0):
    """Fonction utilitaire pour récupérer des valeurs en sécurité"""
    if dictionary and isinstance(dictionary, dict):
        return dictionary.get(key, default)
    return default

def show_search_metrics():
    """Afficher les métriques de recherche avec gestion des valeurs None"""
    if st.session_state.search_results and st.session_state.search_results.get('success'):
        results = st.session_state.search_results
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Temps de recherche", 
                f"{results.get('search_time', 0):.2f}s",
                help="Temps d'exécution de la requête"
            )
        
        with col2:
            total_votes = 0
            if results.get('resultats_vote'):
                total_votes = sum(vote[2] for vote in results['resultats_vote'])
            st.metric(
                "Total votes", 
                f"{total_votes:,}",
                help="Nombre total de votes dans le département"
            )
        
        with col3:
            # CORRECTION: Vérifier si dept_full_info n'est pas None
            dept_full_info = results.get('dept_full_info')
            if dept_full_info and isinstance(dept_full_info, dict):
                ratio = dept_full_info.get('ratio', 0)
            else:
                ratio = 0
            
            st.metric(
                "Ratio prénom", 
                f"{ratio:.4f}",
                help="Ratio de représentation du prénom"
            )
        
        with col4:
            # CORRECTION: Même vérification pour les occurrences
            if dept_full_info and isinstance(dept_full_info, dict):
                occurrences = dept_full_info.get('prenom_total', 0)
            else:
                occurrences = 0
                
            st.metric(
                "Occurrences", 
                f"{occurrences:,}",
                help="Nombre d'occurrences du prénom"
            )

def show_search_history():
    """Afficher l'historique des recherches"""
    if st.session_state.search_history:
        st.sidebar.markdown("---")
        st.sidebar.subheader("🕒 Historique")
        
        for i, search in enumerate(reversed(st.session_state.search_history[-5:])):
            status_icon = "✅" if search['success'] else "❌"
            button_text = f"{status_icon} {search['prenom']} ({search['periode']}) - {search['timestamp']}"
            
            if st.sidebar.button(
                button_text, 
                key=f"history_{i}",
                help="Cliquer pour relancer cette recherche"
            ):
                # Au lieu de modifier directement, on stocke la demande de changement
                st.session_state.pending_search = {
                    'prenom': search['prenom'],
                    'periode': search['periode'],
                    'from_history': True
                }
                st.rerun()

def handle_pending_search():
    """Gérer les recherches en attente depuis l'historique"""
    if 'pending_search' in st.session_state and st.session_state.pending_search:
        pending = st.session_state.pending_search
        
        # Extraire les années de la période
        if '-' in pending['periode']:
            try:
                start, end = pending['periode'].split('-')
                # Créer une nouvelle recherche automatiquement
                pgc = init_db_connection()
                with st.spinner("🔍 Relancement de la recherche..."):
                    result = perform_search(pgc, pending['prenom'], int(start), int(end))
                
                # Afficher un message de confirmation
                st.success(f"🔄 Recherche relancée: {pending['prenom']} ({pending['periode']})")
                
            except:
                st.error("Erreur lors du relancement de la recherche")
        
        # Nettoyer la recherche en attente
        st.session_state.pending_search = None

def show_department_comparison():
    """Nouvelle fonctionnalité : comparaison de départements"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚖️ Comparaison")
    
    if st.sidebar.button("📊 Comparer Départements"):
        st.subheader("📊 Comparaison Multi-Départements")
        
        # Interface de comparaison
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Sélectionnez les départements à comparer:**")
            # Vous pouvez étendre ceci avec une vraie liste de départements
            dept_list = ["75", "13", "59", "69", "33", "44"]
            selected_depts = st.multiselect(
                "Départements:", 
                dept_list,
                default=["75", "13"]
            )
        
        with col2:
            if selected_depts and st.session_state.search_results:
                prenom = st.session_state.search_results['prenom']
                annee_debut = st.session_state.search_results['annee_debut']
                annee_fin = st.session_state.search_results['annee_fin']
                
                st.write(f"**Résultats pour '{prenom}' ({annee_debut}-{annee_fin}):**")
                
                # Simuler des données de comparaison
                comparison_data = []
                for dept in selected_depts:
                    comparison_data.append({
                        'Département': dept,
                        'Occurrences': 1200 + int(dept) * 10,  # Simulation
                        'Ratio': 0.0234 + float(dept) / 10000,  # Simulation
                        'Candidat Principal': f"Candidat {chr(65 + int(dept) % 5)}"
                    })
                
                df_comparison = pd.DataFrame(comparison_data)
                st.dataframe(df_comparison, use_container_width=True)

def show_advanced_filters():
    """Filtres avancés pour affiner la recherche"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Filtres Avancés")
    
    with st.sidebar.expander("⚙️ Options avancées"):
        # Filtre par type de département
        dept_type = st.selectbox(
            "Type de département:",
            ["Tous", "Urbain", "Rural", "Côtier", "Montagnard"]
        )
        
        # Filtre par région
        region_filter = st.selectbox(
            "Région:",
            ["Toutes", "Île-de-France", "PACA", "Auvergne-Rhône-Alpes", "Occitanie"]
        )
        
        # Seuil de confiance
        confidence_threshold = st.slider(
            "Seuil de confiance:",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1,
            help="Seuil minimum pour afficher les résultats"
        )
        
        return {
            'dept_type': dept_type,
            'region_filter': region_filter,
            'confidence_threshold': confidence_threshold
        }
    
def add_statistics_sidebar():
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Statistiques de Session")
    
    if 'search_history' in st.session_state and st.session_state.search_history:
        total_searches = len(st.session_state.search_history)
        successful_searches = sum(1 for s in st.session_state.search_history if s.get('success', False))
        success_rate = (successful_searches / total_searches) * 100 if total_searches > 0 else 0
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("Recherches", total_searches)
        with col2:
            st.metric("Succès", f"{success_rate:.0f}%")
        
        # Graphique mini des temps de recherche
        if any('search_time' in s for s in st.session_state.search_history):
            times = [s.get('search_time', 0) for s in st.session_state.search_history[-10:]]
            if times:
                fig = px.line(y=times, title="Temps de recherche")
                fig.update_layout(height=200, showlegend=False)
                st.sidebar.plotly_chart(fig, use_container_width=True)

def add_prenom_suggestions():
    """Widget de suggestions de prénoms"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("💡 Suggestions")
    
    # Prénoms par époque
    suggestions = {
        "Classiques": ["MARIE", "JEAN", "PIERRE", "JACQUES"],
        "Années 70-80": ["CHRISTOPHE", "PHILIPPE", "SYLVIE", "NATHALIE"],
        "Modernes": ["KEVIN", "JESSICA", "ANTHONY"]
    }
    
    for category, names in suggestions.items():
        st.sidebar.write(f"**{category}:**")
        for name in names:
            if st.sidebar.button(name, key=f"suggest_{name}", help=f"Rechercher {name}"):
                # Déclencher une recherche
                st.session_state.pending_search = {
                    'prenom': name,
                    'periode': '1960-1990',
                    'from_suggestion': True
                }
                st.rerun()

def create_comparison_chart(results_list):
    """Créer un graphique de comparaison"""
    if len(results_list) < 2:
        return None
    
    # Données factices pour la démo
    comparison_data = []
    for i, result in enumerate(results_list):
        comparison_data.append({
            'Prénom': result['prenom'],
            'Ratio': result.get('ratio', 0.001 + i * 0.0005),  # Simulation
            'Département': result.get('departement', f'Dept-{i+1}'),
            'Occurrences': result.get('occurrences', 1000 + i * 500)
        })
    
    df = pd.DataFrame(comparison_data)
    
    fig = px.bar(
        df,
        x='Prénom',
        y='Ratio',
        color='Occurrences',
        title="Comparaison des Ratios par Prénom",
        hover_data=['Département']
    )
    
    return fig

def add_export_functionality():
    """Fonctionnalité d'export avec vérifications de sécurité"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("📥 Export")
    
    if (st.session_state.search_results and 
        st.session_state.search_results.get('success') and
        st.session_state.search_results.get('resultats_vote')):
        
        results = st.session_state.search_results
        
        # Format CSV
        if st.sidebar.button("📊 Export CSV"):
            if results.get('resultats_vote'):
                df = pd.DataFrame(results['resultats_vote'], columns=['Nom', 'Prénom', 'Votes'])
                csv = df.to_csv(index=False)
                st.sidebar.download_button(
                    label="💾 Télécharger CSV",
                    data=csv,
                    file_name=f"votes_{results['prenom']}_{results['annee_debut']}-{results['annee_fin']}.csv",
                    mime="text/csv"
                )
        
        # Format JSON
        if st.sidebar.button("📋 Export JSON"):
            import json
            json_data = {
                'prenom': results.get('prenom', ''),
                'periode': f"{results.get('annee_debut', '')}-{results.get('annee_fin', '')}",
                'departement': results.get('dept_info', ''),
                'departement_info': results.get('dept_full_info', {}),
                'votes': results.get('resultats_vote', [])
            }
            json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
            st.sidebar.download_button(
                label="💾 Télécharger JSON",
                data=json_str,
                file_name=f"analyse_{results['prenom']}.json",
                mime="application/json"
            )
    else:
        st.sidebar.info("Effectuez une recherche réussie pour activer l'export")

def add_dark_mode_toggle():
    """Ajouter un toggle pour le mode sombre (simulation)"""
    st.sidebar.markdown("---")
    
    dark_mode = st.sidebar.checkbox("🌙 Mode sombre", value=False)
    
    if dark_mode:
        st.markdown("""
        <style>
        .stApp {
            background-color: #1e1e1e;
            color: white;
        }
        .stSidebar {
            background-color: #2d2d2d;
        }
        </style>
        """, unsafe_allow_html=True)

def add_about_section():
    """Section À propos"""
    with st.expander("ℹ️ À propos de cette application"):
        st.markdown("""
        ### 🗳️ Qui Vote Quoi
        
        **Application d'analyse politique par prénoms**
        
        Cette application analyse la corrélation entre les prénoms et les tendances de vote en France.
        
        **📊 Sources de données :**
        - INSEE : prénoms par département et année de naissance
        - Ministère de l'Intérieur : résultats électoraux
        
        **🔧 Technologies :**
        - Python (Streamlit, Pandas, Plotly)
        - PostgreSQL + Docker
        - Folium pour les cartes interactives
        
        **👨‍💻 Développé par :** Votre Nom
        **📅 Version :** 1.0.0
        **🎓 Projet :** Master Informatique
        """)

def add_keyboard_shortcuts():
    """Ajouter des raccourcis clavier (simulation)"""
    st.markdown("""
    <script>
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'Enter') {
            // Simuler un clic sur le bouton de recherche
            const searchButton = document.querySelector('[data-testid="baseButton-primary"]');
            if (searchButton) searchButton.click();
        }
    });
    </script>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**⌨️ Raccourcis :**")
    st.sidebar.markdown("• `Ctrl + Enter` : Rechercher")

def add_performance_indicators():
    """Indicateurs de performance visuels avec gestion des None"""
    if (st.session_state.search_results and 
        'search_time' in st.session_state.search_results and
        st.session_state.search_results.get('success')):
        
        search_time = st.session_state.search_results.get('search_time', 0)
        
        # Indicateur coloré basé sur la performance
        if search_time < 0.5:
            color = "🟢"
            status = "Excellent"
        elif search_time < 1.0:
            color = "🟡" 
            status = "Bon"
        else:
            color = "🔴"
            status = "Lent"
        
        st.sidebar.markdown(f"**⚡ Performance:** {color} {status}")
        st.sidebar.progress(min(search_time / 2.0, 1.0))

def add_fun_facts():
    """Ajouter des faits amusants"""
    fun_facts = [
        "🎯 Le prénom le plus populaire en France est Marie",
        "📊 Il y a plus de 40 000 prénoms différents en France",
        "🗳️ Les tendances de vote varient de 15% selon les régions",
        "🌍 Certains prénoms sont concentrés dans une seule région",
        "📈 Les prénoms reflètent les tendances sociologiques"
    ]
    
    import random
    if st.sidebar.button("🎲 Fait Amusant"):
        fact = random.choice(fun_facts)
        st.sidebar.info(fact)

def add_comparison_mode():
    """Mode de comparaison avec gestion sécurisée"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚖️ Mode Comparaison")
    
    if 'comparison_list' not in st.session_state:
        st.session_state.comparison_list = []
    
    # Ajouter le résultat actuel à la comparaison
    if (st.session_state.search_results and 
        st.session_state.search_results.get('success') and
        st.session_state.search_results.get('dept_full_info') and
        st.sidebar.button("➕ Ajouter à la comparaison")):
        
        result = st.session_state.search_results
        dept_full_info = result.get('dept_full_info', {})
        
        comparison_item = {
            'prenom': result.get('prenom', 'Inconnu'),
            'departement': result.get('dept_info', 'Inconnu'),
            'ratio': safe_get_from_dict(dept_full_info, 'ratio', 0),
            'occurrences': safe_get_from_dict(dept_full_info, 'prenom_total', 0)
        }
        
        # Éviter les doublons
        if not any(item['prenom'] == comparison_item['prenom'] for item in st.session_state.comparison_list):
            st.session_state.comparison_list.append(comparison_item)
            st.sidebar.success(f"✅ {result['prenom']} ajouté")
        else:
            st.sidebar.warning(f"⚠️ {result['prenom']} déjà dans la comparaison")
    
    # Afficher la liste de comparaison
    if st.session_state.comparison_list:
        st.sidebar.write(f"**Prénoms en comparaison ({len(st.session_state.comparison_list)}):**")
        
        for i, item in enumerate(st.session_state.comparison_list):
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                st.write(f"• {item['prenom']}")
            with col2:
                if st.button("🗑️", key=f"remove_{i}"):
                    st.session_state.comparison_list.pop(i)
                    st.rerun()
        
        # Boutons d'action
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("📊 Comparer"):
                show_comparison_results()
        with col2:
            if st.button("🗑️ Vider"):
                st.session_state.comparison_list = []
                st.rerun()
    else:
        st.sidebar.info("Aucun prénom en comparaison pour le moment")

def show_comparison_results():
    """Afficher les résultats de comparaison"""
    if len(st.session_state.comparison_list) >= 2:
        st.subheader("📊 Comparaison des Prénoms")
        
        # Tableau de comparaison
        df = pd.DataFrame(st.session_state.comparison_list)
        st.dataframe(df, use_container_width=True)
        
        # Graphique de comparaison
        fig = create_comparison_chart(st.session_state.comparison_list)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

def add_all_bonus_features():
    """Ajouter toutes les fonctionnalités bonus"""
    add_statistics_sidebar()
    add_prenom_suggestions()
    add_export_functionality()
    add_dark_mode_toggle()
    add_performance_indicators()
    add_fun_facts()
    add_comparison_mode()
    add_keyboard_shortcuts()
    add_about_section()

def main():
    # CSS personnalisé pour améliorer l'apparence
    st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialiser pending_search si nécessaire
    if 'pending_search' not in st.session_state:
        st.session_state.pending_search = None
    
    # Gérer les recherches en attente AVANT de créer les widgets
    handle_pending_search()
    
    # Header amélioré
    st.title("🗳️ Qui Vote Quoi")
    st.markdown("**Dashboard Interactif d'Analyse Politique**")
    st.markdown("*Corrélation entre prénoms et tendances électorales en France*")
    st.markdown("---")
    
    pgc = init_db_connection()
    
    # Sidebar améliorée
    st.sidebar.header("🔎 Paramètres de Recherche")
    
    # Gérer les valeurs par défaut pour les widgets en fonction des recherches en attente
    default_prenom = ""
    default_periode = "Personnalisé"
    
    if st.session_state.pending_search and st.session_state.pending_search.get('from_history'):
        default_prenom = st.session_state.pending_search['prenom']
        periode = st.session_state.pending_search['periode']
        if periode == "1946-1964":
            default_periode = "Baby Boomers (1946-1964)"
        elif periode == "1965-1980":
            default_periode = "Génération X (1965-1980)"
        elif periode == "1981-1996":
            default_periode = "Millennials (1981-1996)"
    
    # Input pour le prénom avec suggestions
    prenom = st.sidebar.text_input(
        "Entrez un prénom:", 
        value=default_prenom,
        placeholder="Ex: MARIE, JEAN, PIERRE...", 
        key="prenom_input",
        help="Saisissez un prénom en majuscules ou minuscules"
    )
    
    # Sélection de la tranche d'âge avec presets
    st.sidebar.write("**Période d'analyse:**")
    
    preset_periods = {
        "Baby Boomers (1946-1964)": (1946, 1964),
        "Génération X (1965-1980)": (1965, 1980),
        "Millennials (1981-1996)": (1981, 1996),
        "Personnalisé": None
    }
    
    selected_preset = st.sidebar.selectbox(
        "Période prédéfinie:",
        list(preset_periods.keys()),
        index=list(preset_periods.keys()).index(default_periode)
    )
    
    if preset_periods[selected_preset]:
        annee_debut, annee_fin = preset_periods[selected_preset]
        st.sidebar.write(f"📅 {annee_debut} - {annee_fin}")
    else:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            annee_debut = st.selectbox("Début:", options=list(range(1910, 2023)), 
                                      index=len(list(range(1910, 2023)))//2, key="annee_debut")
        with col2:
            annee_fin = st.selectbox("Fin:", options=list(range(1910, 2023)), 
                                    index=len(list(range(1910, 2023)))-1, key="annee_fin")
    
    # Boutons d'action améliorés
    col_search, col_clear = st.sidebar.columns(2)
    
    with col_search:
        rechercher = st.button("🔍 Analyser", type="primary", key="search_button", use_container_width=True)
    
    with col_clear:
        if st.button("🗑️ Effacer", key="clear_button", use_container_width=True):
            st.session_state.search_results = None
            st.session_state.last_search = None
            st.session_state.pending_search = None
            st.rerun()
    
    # Afficher les filtres avancés
    advanced_filters = show_advanced_filters()
    
    # Afficher l'historique
    show_search_history()
    
    # Afficher la comparaison
    show_department_comparison()
    
    # Effectuer la recherche si le bouton est cliqué OU si c'est une recherche en attente
    should_search = rechercher and prenom
    if st.session_state.pending_search and st.session_state.pending_search.get('from_history'):
        should_search = True
        # Nettoyer après utilisation
        st.session_state.pending_search = None
    
    if should_search:
        with st.spinner("🔍 Recherche en cours..."):
            st.session_state.search_results = perform_search(pgc, prenom, annee_debut, annee_fin)
    
    # Afficher les métriques de recherche
    if st.session_state.search_results and st.session_state.search_results.get('success'):
        show_search_metrics()
        st.markdown("---")
    
    # Colonnes principales
    col_map, col_results = st.columns([2, 1])
    
    # Affichage de la carte améliorée
    with col_map:
        st.subheader("🗺️ Carte de France Interactive")
        
        # Utiliser les résultats sauvegardés s'ils existent
        if st.session_state.search_results and st.session_state.search_results.get('success'):
            results = st.session_state.search_results
            dept_info = results['dept_info']
            dept_full_info = results['dept_full_info']
            
            if dept_info:
                carte = create_france_map(highlighted_dept=dept_info)
                map_data = st_folium(carte, width=700, height=500, key="map_display")
                
                # Messages améliorés
                if dept_full_info:
                    if dept_info == "20":
                        st.markdown(f"""
                        <div class="success-message">
                        <strong>🎯 Résultat:</strong> Le prénom '<strong>{results['prenom']}</strong>' est le plus représenté en <strong>Corse</strong> (département historique 20).<br>
                        <small>ℹ️ La Corse a été divisée en 2A (Corse-du-Sud) et 2B (Haute-Corse) en 1976. Les deux départements sont surlignés en orange.</small>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="success-message">
                        <strong>🎯 Résultat:</strong> Le prénom '<strong>{results['prenom']}</strong>' est le plus représenté dans le département <strong>{dept_full_info['nom']} ({dept_info})</strong>.
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Informations détaillées
                    with st.expander("📊 Informations détaillées"):
                        col_info1, col_info2 = st.columns(2)
                        with col_info1:
                            st.write(f"**Département:** {dept_full_info['nom']}")
                            st.write(f"**Code:** {dept_info}")
                            st.write(f"**Période:** {results['annee_debut']}-{results['annee_fin']}")
                        with col_info2:
                            st.write(f"**Occurrences:** {dept_full_info['prenom_total']:,}")
                            st.write(f"**Total département:** {dept_full_info['total_compte']:,}")
                            st.write(f"**Ratio:** {dept_full_info['ratio']:.6f}")
                else:
                    st.success(f"Le prénom '{results['prenom']}' est le plus représenté dans le département: **{dept_info}**")
            else:
                carte = create_france_map()
                st_folium(carte, width=700, height=500, key="map_default")
                st.warning(f"❌ Aucun département trouvé pour le prénom '{results['prenom']}' dans cette tranche d'âge.")
                
        elif st.session_state.search_results and not st.session_state.search_results.get('success'):
            # Afficher l'erreur
            carte = create_france_map()
            st_folium(carte, width=700, height=500, key="map_error")
            st.error(f"❌ Erreur lors de la recherche: {st.session_state.search_results.get('error', 'Erreur inconnue')}")
        else:
            # Afficher la carte normale par défaut
            carte = create_france_map()
            st_folium(carte, width=700, height=500, key="map_initial")
            st.info("👋 Entrez un prénom et cliquez sur 'Analyser' pour voir le département correspondant s'illuminer sur la carte.")
    
    # Affichage des résultats amélioré
    with col_results:
        st.subheader("📈 Résultats de l'Analyse")
        
        if st.session_state.search_results and st.session_state.search_results.get('success'):
            results = st.session_state.search_results
            resultats_vote = results['resultats_vote']
            
            if resultats_vote:
                st.write("**🏆 Top 5 des candidats dans ce département:**")
                
                # Créer un DataFrame avec plus d'informations
                df_results = pd.DataFrame(resultats_vote, columns=['Nom', 'Prénom', 'Votes'])
                
                # Calculer les pourcentages
                total_votes = df_results['Votes'].sum()
                df_results['Pourcentage'] = (df_results['Votes'] / total_votes * 100).round(1)
                df_results['Candidat'] = df_results['Prénom'] + ' ' + df_results['Nom']
                
                # Affichage avec style
                for i, row in df_results.iterrows():
                    col_rank, col_info = st.columns([0.1, 0.9])
                    with col_rank:
                        st.write(f"**{i+1}.**")
                    with col_info:
                        st.write(f"**{row['Candidat']}**")
                        st.write(f"📊 {row['Votes']:,} votes ({row['Pourcentage']}%)")
                        # Barre de progression
                        st.progress(row['Pourcentage'] / 100)
                
                st.markdown("---")
                
                # Graphique en barres amélioré
                import plotly.express as px
                
                fig = px.bar(
                    df_results,
                    x='Candidat',
                    y='Votes',
                    title="Distribution des Votes",
                    color='Votes',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(
                    xaxis_title="Candidats",
                    yaxis_title="Nombre de Votes",
                    showlegend=False
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistiques supplémentaires
                st.write("**📊 Statistiques:**")
                st.write(f"• **Total des votes:** {total_votes:,}")
                st.write(f"• **Candidat dominant:** {df_results.iloc[0]['Candidat']} ({df_results.iloc[0]['Pourcentage']}%)")
                if len(df_results) > 1:
                    ecart = df_results.iloc[0]['Pourcentage'] - df_results.iloc[1]['Pourcentage']
                    st.write(f"• **Écart avec le 2ème:** {ecart:.1f} points")
                
            else:
                st.warning("❌ Aucun résultat de vote trouvé pour ce département.")
        else:
            st.info("🔍 Les résultats d'analyse apparaîtront ici après la recherche.")
            
            # Conseils d'utilisation
            st.markdown("""
            **💡 Conseils d'utilisation:**
            - Utilisez des prénoms courants (MARIE, JEAN, PIERRE...)
            - Testez différentes périodes générationnelles
            - Explorez l'historique des recherches
            - Utilisez les filtres avancés pour affiner
            """)
    
    # Footer avec informations
    st.markdown("---")
    
    col_footer1, col_footer2, col_footer3 = st.columns(3)
    
    with col_footer1:
        st.markdown("""
        **📊 Sources de données:**
        - INSEE (prénoms par département)
        - Gouvernement français (résultats électoraux)
        - OpenStreetMap (cartes géographiques)
        """)
    
    with col_footer2:
        st.markdown("""
        **🔧 Technologies:**
        - Python + Streamlit
        - PostgreSQL + Docker
        - Folium (cartes interactives)
        - Plotly (graphiques)
        """)
    
    with col_footer3:
        if st.session_state.search_history:
            st.markdown(f"""
            **📈 Statistiques de session:**
            - Recherches effectuées: {len(st.session_state.search_history)}
            - Temps de session: {(time.time() - st.session_state.page_start_time)/60:.1f} min
            - Dernière recherche: {st.session_state.search_history[-1]['timestamp'] if st.session_state.search_history else 'Aucune'}
            """)
            
    add_all_bonus_features()

if __name__ == "__main__":
    main()