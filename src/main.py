import os
import sys
import argparse
from tkinter import Tk, messagebox
from ui.hmi import HMI
import configparser

VERSION = "1.3"
DEBUG_LEVEL = 0                                             
CONFIG_FILE = "config.ini"
ICON_FILE = os.path.join(os.path.dirname(__file__), 'bur.ico') # Path to your icon file

def is_frozen():
    return getattr(sys, 'frozen', False)

def main(project_path=None):
    try:
        root = Tk()
        root.minsize(600, 400)
        
        # Set the application icon
        if os.path.exists(ICON_FILE):
            root.iconbitmap(ICON_FILE)
        else:
            print(f"Icon file '{ICON_FILE}' not found. Using default icon.")

        # Get the path to the configuration file
        exe_path = sys.executable
        exe_dir = os.path.dirname(exe_path)
        if is_frozen():
            cfg_file = os.path.join(exe_dir, CONFIG_FILE)
        else:
            cfg_file = CONFIG_FILE

        # Check if the configuration file exists
        if not os.path.exists(cfg_file):
            messagebox.showerror("Error", f"Configuration file '{cfg_file}' not found.")
            sys.exit(1)  # Exit the application with a non-zero status code

        # Read the configuration file
        config = configparser.ConfigParser()
        config.read(cfg_file)
        DEBUG_LEVEL = int(config.get('GENERAL', 'debug_level'))
        HMI.DEBUG_LEVEL = DEBUG_LEVEL

        # Start HMI
        app = HMI(root, VERSION, DEBUG_LEVEL, cfg_file)

        # Set the project path if provided
        if project_path:
            if not os.path.exists(project_path):
                messagebox.showerror("Error", f"Error: The specified project path '{project_path}' does not exist.")
                sys.exit(1)

            app.project_path_var.set(project_path)
            app.zip_button.grid(row=1, column=0, sticky="e")            
        
        root.mainloop()

    except Exception as e:
        messagebox.showerror("Error", f"General program error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="B&R project file zipper")
    parser.add_argument("project_path", nargs='?', help="Path to the Automation Studio project file (.apj)")
    args = parser.parse_args()

    main(args.project_path)
