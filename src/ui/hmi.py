import tkinter.font as tkFont
from tkinter import Label, Button
from utils.file_handler import open_file
from utils.file_handler import file_apj_handling

class HMI:
    def __init__(self, master, version):
        self.master = master
        master.title(f"B&R project file zipper version {version}")  # Verwenden Sie einen f-String

        self.open_button = Button(master, text="Select Automation Studio project file to zip", command=self.open_file, font=tkFont.Font(size=12))
        self.open_button.pack(anchor="nw", padx=20, pady=20)  # Position the button at the top left with padding

    def open_file(self):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(filetypes=[("Automation Studio Project Files", "*.apj")])
        if file_path:
            print(f"Selected file: {file_path}")  # Placeholder for file handling logic

            # process apj file
            #content = open_file(file_path)
            technology_packages = file_apj_handling(file_path)