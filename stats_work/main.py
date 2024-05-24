import os

def get_name_to_dept(pg_connection, name, date_range):
	sql_file = open("./stats_work/name_to_dept.sql", "r")
	sql_script = sql_file.read()
	sql_file.close()
	sql_script = sql_script.replace("$NAME$", name)
	sql_script = sql_script.replace("$LOWER_DATE_RANGE$", date_range[0])
	sql_script = sql_script.replace("$UPPER_DATE_RANGE$", date_range[1])
	pg_connection.cursor.execute(sql_script)
	return pg_connection.cursor.fetchall()[0][1]

def get_dept_to_vote(pg_connection, dept):
	sql_file = open("./stats_work/dept_to_average_vote.sql", "r")
	sql_script = sql_file.read()
	sql_file.close()
	sql_script = sql_script.replace("$DEPT$", dept)
	print(sql_script)
	pg_connection.cursor.execute(sql_script)
	return pg_connection.cursor.fetchall()


def get_vote(pg_connection, name, date_range):
	dept = get_name_to_dept(pg_connection, name, date_range)
	return get_dept_to_vote(pg_connection, dept)