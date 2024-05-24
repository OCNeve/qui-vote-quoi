from customtkinter import CTk, CTkFrame, CTkLabel, CTkCheckBox, CTkComboBox, CTkEntry, CTkButton, CTkScrollableFrame
from tkinter import StringVar
from stats_work.main import get_vote
from utils.pgconnector import PGConnection
import os

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')

pgc = PGConnection(dotenv_path)
pgc.connect_to_db()



class Root(CTk):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.title("Qui vote quoi")
		main_frame = MainFrame(master=self)
		main_frame.pack(pady=5, padx=5)

class MainFrame(CTkFrame):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.selected_lower_date = StringVar(self) 
		self.selected_upper_date = StringVar(self)
		self.name_entry = CTkEntry 
		self.result_frame = ResultFrame(self)
		self.make_widgets()

	def make_widgets(self):
		label = PrettyLabel(master=self, text="Entrez un prenom:")
		label.pack(pady=5, padx=5)
		self.name_entry = CTkEntry(master=self)
		self.name_entry.pack(pady=5, padx=5)
		button = CTkButton(master=self, text="Rechercher", command=self.get_params)
		button.pack(pady=5, padx=5)
		lower_date_options = list(map(str, range(1910, 2023)))
		upper_date_options = list(map(str, range(1910, 2023)))
		self.selected_lower_date.set(lower_date_options[len(lower_date_options)//2]) 
		self.selected_upper_date.set(upper_date_options[-1]) 
		frame = CTkFrame(self)
		lower_date_choice = CTkComboBox(master=frame, variable=self.selected_lower_date, values=lower_date_options, width=70)
		upper_date_choice = CTkComboBox(master=frame, variable=self.selected_upper_date, values=upper_date_options, width=70)
		frame.pack()
		lower_date_choice.grid(pady=5, padx=5, column=0, row=0)
		upper_date_choice.grid(pady=5, padx=5, column=1, row=0)

	def get_params(self):
		self.result_frame.pack_forget()
		del self.result_frame
		self.result_frame = ResultFrame(self)
		self.result_frame.add_result(get_vote(pgc, self.name_entry.get(), (self.selected_lower_date.get(), self.selected_upper_date.get())))
		self.result_frame.pack()

class PrettyLabel(CTkLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, font=("Ubuntu", 12, 'bold'), **kwargs)

class ResultFrame(CTkScrollableFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, height=10, width=300, **kwargs)
       
    def add_result(self, result_set):
    	labels = []
    	for i, result in enumerate(result_set):
    		labels.append(PrettyLabel(self, text=f"{i+1}. {result[1]} {result[0]}"))

    	list(map(lambda x: x.pack(), labels))


