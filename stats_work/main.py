# stats_work/main.py - Version optimisée simple
import os
import time

# Cache simple en mémoire pour éviter les requêtes identiques
_simple_cache = {}

def get_name_to_dept(pg_connection, name, date_range):
	"""Version avec cache simple en mémoire"""
	cache_key = f"{name}_{date_range[0]}_{date_range[1]}"
	
	# Vérifier le cache d'abord
	if cache_key in _simple_cache:
		print(f"🚀 Cache hit pour {name}")
		return _simple_cache[cache_key]
	
	# Sinon, exécuter la requête normale
	sql_file = open("./stats_work/name_to_dept.sql", "r")
	sql_script = sql_file.read()
	sql_file.close()
	sql_script = sql_script.replace("$NAME$", name)
	sql_script = sql_script.replace("$LOWER_DATE_RANGE$", date_range[0])
	sql_script = sql_script.replace("$UPPER_DATE_RANGE$", date_range[1])
	
	try:
		start_time = time.time()
		pg_connection.cursor.execute(sql_script)
		result = pg_connection.cursor.fetchall()
		query_time = time.time() - start_time
		
		dept_code = result[0][1] if result else None
		
		# Mettre en cache
		_simple_cache[cache_key] = dept_code
		print(f"🔍 Requête {name} exécutée en {query_time:.3f}s et mise en cache")
		
		return dept_code
	except Exception as e:
		print(f"Erreur dans get_name_to_dept: {e}")
		return None

def get_dept_to_vote(pg_connection, dept):
	"""Version avec cache simple pour les votes"""
	cache_key = f"votes_{dept}"
	
	if cache_key in _simple_cache:
		print(f"🚀 Cache hit pour votes département {dept}")
		return _simple_cache[cache_key]
	
	sql_file = open("./stats_work/dept_to_average_vote.sql", "r")
	sql_script = sql_file.read()
	sql_file.close()
	sql_script = sql_script.replace("$DEPT$", dept)
	
	try:
		start_time = time.time()
		pg_connection.cursor.execute(sql_script)
		results = pg_connection.cursor.fetchall()
		query_time = time.time() - start_time
		
		print(f"🔍 Votes département {dept}: {len(results)} candidats en {query_time:.3f}s")
		
		# Mettre en cache
		_simple_cache[cache_key] = results
		
		return results
	except Exception as e:
		print(f"Erreur dans get_dept_to_vote: {e}")
		return []

def get_name_to_dept_full_info(pg_connection, name, date_range):
	"""Version avec cache simple pour les infos complètes"""
	cache_key = f"full_{name}_{date_range[0]}_{date_range[1]}"
	
	if cache_key in _simple_cache:
		return _simple_cache[cache_key]
	
	sql_file = open("./stats_work/name_to_dept.sql", "r")
	sql_script = sql_file.read()
	sql_file.close()
	sql_script = sql_script.replace("$NAME$", name)
	sql_script = sql_script.replace("$LOWER_DATE_RANGE$", date_range[0])
	sql_script = sql_script.replace("$UPPER_DATE_RANGE$", date_range[1])
	
	try:
		pg_connection.cursor.execute(sql_script)
		result = pg_connection.cursor.fetchall()
		if result:
			dept_name = result[0][0] if result[0][0] else get_department_name_by_code(result[0][1])
			
			full_info = {
				'nom': dept_name,
				'numero': result[0][1],
				'departement_id': result[0][2],
				'prenom_total': result[0][3],
				'total_compte': result[0][4],
				'ratio': result[0][5]
			}
			
			# Mettre en cache
			_simple_cache[cache_key] = full_info
			return full_info
		return None
	except Exception as e:
		print(f"Erreur dans get_name_to_dept_full_info: {e}")
		return None

def get_vote(pg_connection, name, date_range):
	"""Version avec mesure de performance"""
	start_time = time.time()
	print(f"🔍 Début recherche pour {name} ({date_range[0]}-{date_range[1]})")
	
	dept = get_name_to_dept(pg_connection, name, date_range)
	
	if dept:
		votes = get_dept_to_vote(pg_connection, dept)
		total_time = time.time() - start_time
		print(f"✅ Recherche terminée en {total_time:.3f}s - {len(votes)} candidats trouvés")
		return votes
	else:
		total_time = time.time() - start_time
		print(f"❌ Aucun résultat en {total_time:.3f}s")
		return []

def clear_cache():
	"""Nettoyer le cache si nécessaire"""
	global _simple_cache
	_simple_cache.clear()
	print("🗑️ Cache nettoyé")

def get_cache_stats():
	"""Statistiques du cache"""
	return {
		'entries': len(_simple_cache),
		'keys': list(_simple_cache.keys())[:5]
	}

def get_department_name_by_code(dept_code):
	"""Noms des départements - version simplifiée"""
	names = {
		"20": "Corse (historique)",
		"2A": "Corse-du-Sud", 
		"2B": "Haute-Corse",
		"75": "Paris",
		"13": "Bouches-du-Rhône",
		"69": "Rhône",
		"59": "Nord",
		"33": "Gironde"
	}
	
	return names.get(dept_code, f"Département {dept_code}")

# Prénoms populaires pour les suggestions
POPULAR_NAMES = [
	"MARIE", "JEAN", "PIERRE", "MICHEL", "ANDRÉ", "PHILIPPE", 
	"ALAIN", "BERNARD", "CHRISTOPHE", "FRANÇOIS", "DANIEL", "PATRICK"
]