import os
import sys
import argparse
import configparser
from tkinter import Tk, messagebox
from ui.hmi import HMI
from utils.file_handler import process_files

VERSION = "1.5"
DEBUG_LEVEL = 0                                             
CONFIG_FILE = "config.ini"
ICON_FILE = os.path.join(os.path.dirname(__file__), 'bur.ico') # Path to your icon file

def is_frozen():
    return getattr(sys, 'frozen', False)

def main(project_path=None, 
         headless=False, 
         debug_level=None, 
         separate_update_files=None, 
         include_runtime_updates=None, 
         include_technology_updates=None, 
         include_hardware_updates=None, 
         include_as_updates=None, 
         include_binary_folder=None, 
         include_diag_folder=None, 
         include_temp_folder=None, 
         include_dot_folder=None):
    
    try:
        # Create the main window
        if not headless:
            root = Tk()
            root.minsize(600, 400)
            
            # Set the application icon
            if os.path.exists(ICON_FILE):
                root.iconbitmap(ICON_FILE)
            else:
                print(f"Icon file '{ICON_FILE}' not found. Using default icon.")
        else:
            if project_path is None:
                print("Error: Project path not provided in headless mode.")
                sys.exit(0)

        # Get the path to the configuration file
        exe_path = sys.executable
        exe_dir = os.path.dirname(exe_path)
        if is_frozen():
            cfg_file = os.path.join(exe_dir, CONFIG_FILE)
        else:
            cfg_file = CONFIG_FILE

        # Check if the configuration file exists
        if not os.path.exists(cfg_file):
            if not headless:
                messagebox.showerror("Error", f"Configuration file '{cfg_file}' not found.")
            else:
                print(f"Error: Configuration file '{cfg_file}' not found.")
            sys.exit(0)  # Exit the application with a non-zero status code

        # Read the configuration file
        config = configparser.ConfigParser()
        config.read(cfg_file)

        # Override configuration with command line arguments if provided
        if debug_level is not None:
            config['GENERAL']['debug_level'] = str(debug_level)
        if separate_update_files is not None:
            config['GENERAL']['separate_update_files'] = str(separate_update_files)
        if include_runtime_updates is not None:
            config['GENERAL']['include_runtime_updates'] = str(include_runtime_updates)
        if include_technology_updates is not None:
            config['GENERAL']['include_technology_updates'] = str(include_technology_updates)
        if include_hardware_updates is not None:
            config['GENERAL']['include_hardware_updates'] = str(include_hardware_updates)
        if include_as_updates is not None:
            config['GENERAL']['include_as_updates'] = str(include_as_updates)
        if include_binary_folder is not None:
            config['GENERAL']['include_binary_folder'] = str(include_binary_folder)
        if include_diag_folder is not None:
            config['GENERAL']['include_diag_folder'] = str(include_diag_folder)
        if include_temp_folder is not None:
            config['GENERAL']['include_temp_folder'] = str(include_temp_folder)
        if include_dot_folder is not None:
            config['GENERAL']['include_dot_folder'] = str(include_dot_folder)

        if not headless:
            # Start HMI
            app = HMI(root, config, VERSION)

            # Set the project path if provided
            if project_path:
                if not os.path.exists(project_path):
                    messagebox.showerror("Error", f"Error: The specified project path '{project_path}' does not exist.")
                    sys.exit(0)

                app.project_path_var.set(project_path)
                app.zip_button.grid(row=1, column=0, sticky="e")            

            root.mainloop()
        else:
            # Start the zipper in headless mode
            process_files(config, project_path, None)

    except Exception as e:
        if not headless:
            messagebox.showerror("Error", f"General program error: {e}")
        else:
            print(f"General program error: {e}")

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="B&R project file zipper")
        parser.add_argument("project_path", nargs='?', help="Path to the Automation Studio project file (.apj)")
        parser.add_argument("--headless", action="store_true", help="Run in headless mode without GUI")
        parser.add_argument("--debug_level", type=int, help="Set the debug level")
        parser.add_argument("--separate_update_files", nargs='?', const=True, type=lambda x: x.lower() == 'true' if x else True, help="Separate update files into a different zip")
        parser.add_argument("--include_runtime_updates", nargs='?', const=True, type=lambda x: x.lower() == 'true' if x else True, help="Include runtime updates")
        parser.add_argument("--include_technology_updates", nargs='?', const=True, type=lambda x: x.lower() == 'true' if x else True, help="Include technology updates")
        parser.add_argument("--include_hardware_updates", nargs='?', const=True, type=lambda x: x.lower() == 'true' if x else True, help="Include hardware updates")
        parser.add_argument("--include_as_updates", nargs='?', const=True, type=lambda x: x.lower() == 'true' if x else True, help="Include Automation Studio updates")
        parser.add_argument("--include_binary_folder", nargs='?', const=True, type=lambda x: x.lower() == 'true' if x else True, help="Include binary folder")
        parser.add_argument("--include_diag_folder", nargs='?', const=True, type=lambda x: x.lower() == 'true' if x else True, help="Include diagnosis folder")
        parser.add_argument("--include_temp_folder", nargs='?', const=True, type=lambda x: x.lower() == 'true' if x else True, help="Include temp folder")
        parser.add_argument("--include_dot_folder", nargs='?', const=True, type=lambda x: x.lower() == 'true' if x else True, help="Include dot folders")
        args = parser.parse_args()

        main(args.project_path, args.headless, args.debug_level, args.separate_update_files, args.include_runtime_updates, args.include_technology_updates, args.include_hardware_updates, args.include_as_updates, args.include_binary_folder, args.include_diag_folder, args.include_temp_folder, args.include_dot_folder)

    except Exception as e:
        if not args.headless:
            messagebox.showerror("Error", f"General program error: {e}")
        else:
            print(f"General program error: {e}")