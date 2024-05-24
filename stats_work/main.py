from pgconnector import PGConnection
import os

def get_name_to_dept(pg_connection, name, date_range):
	sql_file = open("./stats_work/name_to_dept.sql", "r")
	sql_script = sql_file.read()
	sql_file.close()
	sql_script = sql_script.replace("$NAME$", name)
	sql_script = sql_script.replace("$LOWER_DATE_RANGE$", date_range[0])
	sql_script = sql_script.replace("$UPPER_DATE_RANGE$", date_range[1])
	pg_connection.cursor.execute(sql_script)
	print(pg_connection.cursor.fetchall())

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')

pgc = PGConnection(dotenv_path)
pgc.connect_to_db()

get_name_to_dept(pgc, 'OLIVIER', (1995, 2005))