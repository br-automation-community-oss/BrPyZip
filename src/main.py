import os
import sys
import argparse
import configparser
from tkinter import Tk, messagebox
from ui.hmi import HMI
from utils.file_handler import process_files
from typing import Optional

VERSION = "1.5"
DEBUG_LEVEL = 0                                             
CONFIG_FILE = "config.ini"
ICON_FILE = os.path.join(os.path.dirname(__file__), 'bur.ico') # Path to your icon file

# Configuration keys
DEBUG_LEVEL_KEY = 'debug_level'
SEPARATE_UPDATE_FILES_KEY = 'separate_update_files'
INCLUDE_RUNTIME_UPDATES_KEY = 'include_runtime_updates'
INCLUDE_TECHNOLOGY_UPDATES_KEY = 'include_technology_updates'
INCLUDE_HARDWARE_UPDATES_KEY = 'include_hardware_updates'
INCLUDE_AS_UPDATES_KEY = 'include_as_updates'
INCLUDE_BINARY_FOLDER_KEY = 'include_binary_folder'
INCLUDE_DIAG_FOLDER_KEY = 'include_diag_folder'
INCLUDE_TEMP_FOLDER_KEY = 'include_temp_folder'
INCLUDE_DOT_FOLDER_KEY = 'include_dot_folder'

def is_frozen() -> bool:
    """
    Check if the application is running in a frozen state (e.g., packaged with PyInstaller).
    """
    return getattr(sys, 'frozen', False)

def load_config(cfg_file: str) -> configparser.ConfigParser:
    """
    Load the configuration file.

    Args:
        cfg_file (str): Path to the configuration file.

    Returns:
        configparser.ConfigParser: Loaded configuration.
    """
    config = configparser.ConfigParser()
    config.read(cfg_file)
    return config

def override_config_with_args(config: configparser.ConfigParser, args: argparse.Namespace) -> None:
    """
    Override configuration values with command line arguments if provided.

    Args:
        config (configparser.ConfigParser): Configuration to override.
        args (argparse.Namespace): Command line arguments.
    """
    if args.debug_level is not None:
        config['GENERAL'][DEBUG_LEVEL_KEY] = str(args.debug_level)
    if args.separate_update_files is not None:
        config['GENERAL'][SEPARATE_UPDATE_FILES_KEY] = str(args.separate_update_files)
    if args.include_runtime_updates is not None:
        config['GENERAL'][INCLUDE_RUNTIME_UPDATES_KEY] = str(args.include_runtime_updates)
    if args.include_technology_updates is not None:
        config['GENERAL'][INCLUDE_TECHNOLOGY_UPDATES_KEY] = str(args.include_technology_updates)
    if args.include_hardware_updates is not None:
        config['GENERAL'][INCLUDE_HARDWARE_UPDATES_KEY] = str(args.include_hardware_updates)
    if args.include_as_updates is not None:
        config['GENERAL'][INCLUDE_AS_UPDATES_KEY] = str(args.include_as_updates)
    if args.include_binary_folder is not None:
        config['GENERAL'][INCLUDE_BINARY_FOLDER_KEY] = str(args.include_binary_folder)
    if args.include_diag_folder is not None:
        config['GENERAL'][INCLUDE_DIAG_FOLDER_KEY] = str(args.include_diag_folder)
    if args.include_temp_folder is not None:
        config['GENERAL'][INCLUDE_TEMP_FOLDER_KEY] = str(args.include_temp_folder)
    if args.include_dot_folder is not None:
        config['GENERAL'][INCLUDE_DOT_FOLDER_KEY] = str(args.include_dot_folder)

def create_main_window() -> Tk:
    """
    Create the main Tkinter window.

    Returns:
        Tk: The main Tkinter window.
    """
    root = Tk()
    root.minsize(600, 400)
    if os.path.exists(ICON_FILE):
        root.iconbitmap(ICON_FILE)
    else:
        print(f"Icon file '{ICON_FILE}' not found. Using default icon.")
    return root

def main(project_path: Optional[str] = None, 
         headless: bool = False, 
         debug_level: Optional[int] = None, 
         separate_update_files: Optional[bool] = None, 
         include_runtime_updates: Optional[bool] = None, 
         include_technology_updates: Optional[bool] = None, 
         include_hardware_updates: Optional[bool] = None, 
         include_as_updates: Optional[bool] = None, 
         include_binary_folder: Optional[bool] = None, 
         include_diag_folder: Optional[bool] = None, 
         include_temp_folder: Optional[bool] = None, 
         include_dot_folder: Optional[bool] = None) -> None:
    """
    Main function to run the application.

    Args:
        project_path (Optional[str]): Path to the Automation Studio project file.
        headless (bool): Run in headless mode without GUI.
        debug_level (Optional[int]): Set the debug level.
        separate_update_files (Optional[bool]): Separate update files into a different zip.
        include_runtime_updates (Optional[bool]): Include runtime updates.
        include_technology_updates (Optional[bool]): Include technology updates.
        include_hardware_updates (Optional[bool]): Include hardware updates.
        include_as_updates (Optional[bool]): Include Automation Studio updates.
        include_binary_folder (Optional[bool]): Include binary folder.
        include_diag_folder (Optional[bool]): Include diagnosis folder.
        include_temp_folder (Optional[bool]): Include temp folder.
        include_dot_folder (Optional[bool]): Include dot folders.
    """
    try:
        if not headless:
            root = create_main_window()
        else:
            if project_path is None:
                print("Error: Project path not provided in headless mode.")
                sys.exit(0)

        exe_path = sys.executable
        exe_dir = os.path.dirname(exe_path)
        cfg_file = os.path.join(exe_dir, CONFIG_FILE) if is_frozen() else CONFIG_FILE

        if not os.path.exists(cfg_file):
            error_message = f"Configuration file '{cfg_file}' not found."
            if not headless:
                messagebox.showerror("Error", error_message)
            else:
                print(f"Error: {error_message}")
            sys.exit(0)

        config = load_config(cfg_file)
        override_config_with_args(config, argparse.Namespace(
            debug_level=debug_level,
            separate_update_files=separate_update_files,
            include_runtime_updates=include_runtime_updates,
            include_technology_updates=include_technology_updates,
            include_hardware_updates=include_hardware_updates,
            include_as_updates=include_as_updates,
            include_binary_folder=include_binary_folder,
            include_diag_folder=include_diag_folder,
            include_temp_folder=include_temp_folder,
            include_dot_folder=include_dot_folder
        ))

        if not headless:
            app = HMI(root, config, VERSION)
            if project_path:
                if not os.path.exists(project_path):
                    messagebox.showerror("Error", f"Error: The specified project path '{project_path}' does not exist.")
                    sys.exit(0)
                app.project_path_var.set(project_path)
                app.zip_button.grid(row=1, column=0, sticky="e")
            root.mainloop()
        else:
            process_files(config, project_path, None)

    except Exception as e:
        error_message = f"General program error: {e}"
        if not headless:
            messagebox.showerror("Error", error_message)
        else:
            print(error_message)

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
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
    return parser.parse_args()

if __name__ == "__main__":
    try:
        args = parse_arguments()
        main(args.project_path, args.headless, args.debug_level, args.separate_update_files, args.include_runtime_updates, args.include_technology_updates, args.include_hardware_updates, args.include_as_updates, args.include_binary_folder, args.include_diag_folder, args.include_temp_folder, args.include_dot_folder)
    except Exception as e:
        error_message = f"General program error: {e}"
        if not args.headless:
            messagebox.showerror("Error", error_message)
        else:
            print(error_message)