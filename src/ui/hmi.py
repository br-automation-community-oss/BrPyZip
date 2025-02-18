import tkinter as tk
import tkinter.font as tkFont
import configparser
import os
from tkinter import Label, Button, Entry, Frame, Checkbutton, IntVar, messagebox, Toplevel, StringVar, ttk, Text, Scrollbar, filedialog
from utils.file_handler import process_files  # Assuming this import is correct
from datetime import datetime

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        if self.tooltip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip_window = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = Label(tw, text=self.text, justify='left',
                      background="#ffffe0", relief='solid', borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event):
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            tw.destroy()

class HMI:
    def __init__(self, master, VERSION):
        self.master = master
        self.VERSION = VERSION  # Store VERSION as an instance variable
        self.DEBUG_LEVEL = 2
        self.cancelled = False
        master.title(f"B&R project file zipper version {VERSION}")

        self.config = configparser.ConfigParser()
        self.config.read("config.ini")

        INCLUDE_BINARY = self.config.getboolean('GENERAL', 'include_binary_folder', fallback=False)
        INCLUDE_DIAG = self.config.getboolean('GENERAL', 'include_diag_folder', fallback=False)
        INCLUDE_TEMP = self.config.getboolean('GENERAL', 'include_temp_folder', fallback=False)
        INCLUDE_DOT = self.config.getboolean('GENERAL', 'include_dot', fallback=False)
        SEPARATE_UPDATE_FILES = self.config.getboolean('GENERAL', 'separate_update_files', fallback=False)
        INCLUDE_RUNTIME_UPDATES = self.config.getboolean('GENERAL', 'include_runtime_updates', fallback=True)
        INCLUDE_TECHNOLOGY_UPDATES = self.config.getboolean('GENERAL', 'include_technology_updates', fallback=True)
        INCLUDE_HARDWARE_UPDATES = self.config.getboolean('GENERAL', 'include_hardware_updates', fallback=True)
        INCLUDE_AS_UPDATES = self.config.getboolean('GENERAL', 'include_as_updates', fallback=False)
        self.file_path = self.config.get('GENERAL', 'last_path', fallback=False)

        # Frame for label and entry
        path_frame = Frame(master)
        path_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        self.label = Label(path_frame, text="Project Path:", font=tkFont.Font(size=11))
        self.label.grid(row=0, column=0, sticky="w")

        if self.file_path and os.path.exists(self.file_path):
            self.project_path_var = StringVar(value=self.file_path)
        else:
            self.project_path_var = StringVar(value='')

        self.project_path = Entry(path_frame, font=tkFont.Font(size=10), textvariable=self.project_path_var, width=50)
        self.project_path.grid(row=0, column=1, sticky="ew")
        Tooltip(self.project_path, "Enter the path to your Automation Studio project here.")
        path_frame.columnconfigure(1, weight=1)  # Entry expands within its frame

        # Add the progress bar
        self.progress = ttk.Progressbar(path_frame, orient="horizontal", length=200, mode="determinate")
        self.progress.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky="ew")

        # Frame for the button
        button_frame = Frame(master)
        button_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="e")

        # Set a fixed width for the buttons
        button_width = 15

        self.open_button = Button(button_frame, text="Open Project", command=self.open_file, font=tkFont.Font(size=11), width=button_width)
        self.open_button.grid(row=0, column=0, sticky="e")
        Tooltip(self.open_button, "Select the path to your Automation Studio project.")

        # Add the ZIP button
        self.zip_button = Button(button_frame, text="ZIP", command=self.zip_project, font=tkFont.Font(size=11), width=button_width)
        self.zip_button.grid(row=1, column=0, sticky="e")
        Tooltip(self.zip_button, "Zip the selected project.")
        if self.file_path == "":
            self.zip_button.grid_forget()

        # Add the Cancel button
        self.cancel_button = Button(button_frame, text="Cancel", command=self.cancel_process, font=tkFont.Font(size=11), width=button_width)
        Tooltip(self.cancel_button, "Cancel the ongoing process.")

        # Add the Save Log button (initially hidden)
        self.save_log_button = Button(button_frame, text="Save Log", command=self.save_log, font=tkFont.Font(size=11), width=button_width)
        Tooltip(self.save_log_button, "Save the log to a file.")
        self.save_log_button.grid(row=2, column=0, sticky="e")
        self.save_log_button.grid_remove()

        master.columnconfigure(0, weight=1)  # Make the path_frame (and thus the entry) expand

        checkbox_frame = Frame(master)
        checkbox_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="w") #span both columns

        self.include_binary_var = IntVar(value=1 if INCLUDE_BINARY else 0)
        self.include_binary_checkbox = Checkbutton(checkbox_frame, text="Include binary folder", variable=self.include_binary_var, command=self.on_include_binary_checkbox_change)
        self.include_binary_checkbox.grid(row=0, column=1, sticky="w")
        Tooltip(self.include_binary_checkbox, "Include the binary folder in the ZIP file.")

        self.include_diagnostic_var = IntVar(value=1 if INCLUDE_DIAG else 0)
        self.include_diagnostic_checkbox = Checkbutton(checkbox_frame, text="Include diagnostic folder", variable=self.include_diagnostic_var, command=self.on_include_diagnostic_checkbox_change)
        self.include_diagnostic_checkbox.grid(row=1, column=1, sticky="w")
        Tooltip(self.include_diagnostic_checkbox, "Include the diagnostic folder in the ZIP file.")

        self.include_temp_var = IntVar(value=1 if INCLUDE_TEMP else 0)
        self.include_temp_checkbox = Checkbutton(checkbox_frame, text="Include temp folder", variable=self.include_temp_var, command=self.on_include_temp_checkbox_change)
        self.include_temp_checkbox.grid(row=2, column=1, sticky="w")
        Tooltip(self.include_temp_checkbox, "Include the temp folder in the ZIP file.")

        self.include_dot_var = IntVar(value=1 if INCLUDE_DOT else 0)
        self.include_dot_checkbox = Checkbutton(checkbox_frame, text="Include dot folder", variable=self.include_dot_var, command=self.on_include_dot_checkbox_change)
        self.include_dot_checkbox.grid(row=3, column=1, sticky="w")
        Tooltip(self.include_dot_checkbox, "Include folders that start with a '.' in the ZIP file. (e.g. .git)")

        self.include_runtime_updates_var = IntVar(value=1 if INCLUDE_RUNTIME_UPDATES else 0)
        self.include_runtime_updates_checkbox = Checkbutton(checkbox_frame, text="Include runtime updates", variable=self.include_runtime_updates_var, command=self.on_include_runtime_updates_checkbox_change)
        self.include_runtime_updates_checkbox.grid(row=0, column=0, sticky="w")
        Tooltip(self.include_runtime_updates_checkbox, "Include runtime updates in the ZIP file.")

        self.include_technology_updates_var = IntVar(value=1 if INCLUDE_TECHNOLOGY_UPDATES else 0)
        self.include_technology_updates_checkbox = Checkbutton(checkbox_frame, text="Include technology updates", variable=self.include_technology_updates_var, command=self.on_include_technology_updates_checkbox_change)
        self.include_technology_updates_checkbox.grid(row=1, column=0, sticky="w")
        Tooltip(self.include_technology_updates_checkbox, "Include technology updates in the ZIP file.")

        self.include_hardware_updates_var = IntVar(value=1 if INCLUDE_HARDWARE_UPDATES else 0)
        self.include_hardware_updates_checkbox = Checkbutton(checkbox_frame, text="Include hardware updates", variable=self.include_hardware_updates_var, command=self.on_include_hardware_updates_checkbox_change)
        self.include_hardware_updates_checkbox.grid(row=2, column=0, sticky="w")
        Tooltip(self.include_hardware_updates_checkbox, "Include hardware updates in the ZIP file.")

        self.include_as_updates_var = IntVar(value=1 if INCLUDE_AS_UPDATES else 0)
        self.include_as_updates_checkbox = Checkbutton(checkbox_frame, text="Include Automation Studio updates", variable=self.include_as_updates_var, command=self.on_include_as_updates_checkbox_change)
        self.include_as_updates_checkbox.grid(row=3, column=0, sticky="w")
        Tooltip(self.include_as_updates_checkbox, "Include Automation Studio updates in the ZIP file.")

        self.separate_update_files_var = IntVar(value=1 if SEPARATE_UPDATE_FILES else 0)
        self.separate_update_files_checkbox = Checkbutton(checkbox_frame, text="Separate upgrades zip file", variable=self.separate_update_files_var, command=self.on_separate_update_files_checkbox_change)
        self.separate_update_files_checkbox.grid(row=4, column=0, sticky="w")
        Tooltip(self.separate_update_files_checkbox, "Create a separate ZIP file for upgrades.")

        # --- Scrollable Log Text Area ---
        log_frame = Frame(master)  # Create a frame to hold the Text and Scrollbar
        log_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=20, sticky="nsew")

        self.log_text = Text(log_frame, font=tkFont.Font(size=8), wrap="word", state="disabled", bg="white", relief="sunken")  # Use Text widget
        self.log_text.grid(row=0, column=0, sticky="nsew")

        log_scrollbar = Scrollbar(log_frame, command=self.log_text.yview)  # Create Scrollbar
        log_scrollbar.grid(row=0, column=1, sticky="ns")

        self.log_text['yscrollcommand'] = log_scrollbar.set  # Connect Scrollbar to Text widget

        log_frame.columnconfigure(0, weight=1)  # Make Text widget expand
        log_frame.rowconfigure(0, weight=1)    # Make Text widget expand

        master.rowconfigure(2, weight=1)  # Make log_frame expand vertically
        master.columnconfigure(0, weight=1)  # Make log_frame expand horizontally
        master.columnconfigure(1, weight=0)

    # Handle open file dialog
    def open_file(self):
        """
        Opens a file dialog for the user to select an Automation Studio Project file (.apj).
        This method uses the tkinter filedialog to prompt the user to select a file with the 
        extension .apj. If a file is selected, it logs the selected file path if debugging is enabled 
        and then processes the file.
        Returns:
            None
        """
        self.file_path = filedialog.askopenfilename(filetypes=[("Automation Studio Project Files", "*.apj")])
        if self.file_path:
            if self.DEBUG_LEVEL > 0:
                self.create_log(f"Selected file: {self.file_path}")
            
            # Save the selected file path to the config file
            self.config.set('GENERAL', 'last_path', self.file_path)
            with open ('config.ini', 'w') as configfile:
                self.config.write(configfile)
            
            # Update the project_path entry with the selected file path
            self.project_path_var.set(self.file_path)
            self.zip_button.grid(row=1, column=0, sticky="e")

    # Handle zipping the project
    def zip_project(self):
        """
        Zips the selected project.
        This method should contain the logic to zip the project files.
        Returns:
            None
        """
        project_path = self.project_path_var.get()
        if not project_path:
            self.create_error("No project path specified.")
            return

        # Hide the buttons while processing
        self.open_button.grid_forget()
        self.zip_button.grid_forget()
        self.save_log_button.grid_forget()
        self.cancel_button.grid(row=1, column=0, sticky="e")
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")  # Clear the log
        self.log_text.configure(state="disabled")
        self.progress['value'] = 0

        # Refresh the window
        self.master.update()

        self.cancelled = False
        self.create_log(f"Starting with version {self.VERSION}")
        process_files(project_path, self)

        # Show the buttons again
        self.open_button.grid(row=0, column=0, sticky="e")
        self.zip_button.grid(row=1, column=0, sticky="e")
        self.cancel_button.grid_forget()
        self.save_log_button.grid()

        # Open the directory containing the ZIP file
        zip_file_path = os.path.dirname(project_path)
        if os.path.exists(zip_file_path):
            os.startfile(os.path.dirname(zip_file_path))

    def cancel_process(self):
        """
        Cancels the ongoing process.
        """
        self.cancelled = True
        self.create_log("Process cancelled by user.")

    # Log window entries
    def create_log(self, log_text):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{current_time} - {log_text}\n"

        self.log_text.configure(state="normal")  # Enable editing temporarily
        self.log_text.insert("end", log_entry)    # Insert the new log entry
        self.log_text.configure(state="disabled") # Disable editing again
        self.log_text.see("end") # Autoscroll to the end
        
        # Refresh the window
        self.master.update()

    # Create an error popup
    def create_error(self, error_text):
        """
        Creates a popup with the provided error text.

        Args:
            error_text (str): The error text to be displayed.

        Returns:
            None
        """
        self.create_log(f"ERROR: {error_text}")
        messagebox.showerror("Error", error_text)

    def on_include_binary_checkbox_change(self):
        if self.include_binary_var.get() == 1:
            self.config.set('GENERAL', 'include_binary_folder', "True")
        else:
            self.config.set('GENERAL', 'include_binary_folder', "False")
        with open ('config.ini', 'w') as configfile:
            self.config.write(configfile)

    def on_include_diagnostic_checkbox_change(self):
        if self.include_diagnostic_var.get() == 1:
            self.config.set('GENERAL', 'include_diag_folder', "True")
        else:
            self.config.set('GENERAL', 'include_diag_folder', "False")
        with open ('config.ini', 'w') as configfile:
            self.config.write(configfile)

    def on_include_temp_checkbox_change(self):
        if self.include_temp_var.get() == 1:
            self.config.set('GENERAL', 'include_temp_folder', "True")
        else:
            self.config.set('GENERAL', 'include_temp_folder', "False")
        with open ('config.ini', 'w') as configfile:
            self.config.write(configfile)

    def on_separate_update_files_checkbox_change(self):
        if self.separate_update_files_var.get() == 1:
            self.config.set('GENERAL', 'separate_update_files', "True")
        else:
            self.config.set('GENERAL', 'separate_update_files', "False")
        with open ('config.ini', 'w') as configfile:
            self.config.write(configfile)

    def on_include_runtime_updates_checkbox_change(self):
        if self.include_runtime_updates_var.get() == 1:
            self.config.set('GENERAL', 'include_runtime_updates', "True")
        else:
            self.config.set('GENERAL', 'include_runtime_updates', "False")
        with open ('config.ini', 'w') as configfile:
            self.config.write(configfile)

    def on_include_technology_updates_checkbox_change(self):
        if self.include_technology_updates_var.get() == 1:
            self.config.set('GENERAL', 'include_technology_updates', "True")
        else:
            self.config.set('GENERAL', 'include_technology_updates', "False")
        with open ('config.ini', 'w') as configfile:
            self.config.write(configfile)

    def on_include_hardware_updates_checkbox_change(self):
        if self.include_hardware_updates_var.get() == 1:
            self.config.set('GENERAL', 'include_hardware_updates', "True")
        else:
            self.config.set('GENERAL', 'include_hardware_updates', "False")
        with open ('config.ini', 'w') as configfile:
            self.config.write(configfile)

    def on_include_dot_checkbox_change(self):
        if self.include_dot_var.get() == 1:
            self.config.set('GENERAL', 'include_dot', "True")
        else:
            self.config.set('GENERAL', 'include_dot', "False")
        with open ('config.ini', 'w') as configfile:
            self.config.write(configfile)

    def on_include_as_updates_checkbox_change(self):
        if self.include_as_updates_var.get() == 1:
            self.config.set('GENERAL', 'include_as_updates', "True")
        else:
            self.config.set('GENERAL', 'include_as_updates', "False")
        with open ('config.ini', 'w') as configfile:
            self.config.write(configfile)

    def save_log(self):
        """
        Saves the log text to a file.
        """
        log_content = self.log_text.get("1.0", "end-1c")
        if log_content:
            file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
            if file_path:
                with open(file_path, 'w') as file:
                    file.write(log_content)
                self.create_log(f"Log saved to {file_path}")