import sys
import time

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


if len(sys.argv) == 1:
	print('Argument required. Use help to list arguments.')
else:
	if sys.argv[1] == "import":
		print('importing data')
		from data_dumper.main import _import
		if not (len(argv) == 3 and argv[2] == "-y"):
			remake_database()
		_import()
	elif sys.argv[1] == "desktopui":
		from tkui.main import Root
		root = Root()
		root.mainloop()
	elif sys.argv[1] == "webserver":
		print('starting webserver')
	elif sys.argv[1] == "cli":
		print('starting cli')
	else:
		print("Possible arguments are as follows:")
		print("\timport:   \timport and dump data into the database")
		print("\tdesktopui:\tstartup a tkinter GUI")
		print("\twebserver:\tstartup a webserver to server apis")
		print("\tcli:      \tstartup a cli")




