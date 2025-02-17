import os
import sys
from tkinter import Tk
from ui.hmi import HMI
import configparser

VERSION = "1.0.0"
DEBUG_LEVEL = 0                                             
CONFIG_FILE = "config.ini"
ICON_FILE = os.path.join(os.path.dirname(__file__), 'bur.ico') # Path to your icon file

if __name__ == "__main__":
    root = Tk()
    root.minsize(600, 400)
    
    # Set the application icon
    if os.path.exists(ICON_FILE):
        root.iconbitmap(ICON_FILE)
    else:
        print(f"Icon file '{ICON_FILE}' not found. Using default icon.")

    app = HMI(root, VERSION)

    # Check if the configuration file exists
    if not os.path.exists(CONFIG_FILE):
        app.create_error(f"Configuration file '{CONFIG_FILE}' not found.")
        sys.exit(1)  # Exit the application with a non-zero status code

    # Read the configuration file
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    DEBUG_LEVEL = int(config.get('GENERAL', 'debug_level'))
    HMI.DEBUG_LEVEL = DEBUG_LEVEL
    
    root.mainloop()
