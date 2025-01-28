from tkinter import Tk
from ui.hmi import HMI

VERSION = "1.0.0"
AS_PATH = "C:\Program Files\BRAutomation4"

if __name__ == "__main__":

    root = Tk()
    root.minsize(400, 200)
    app = HMI(root, VERSION)
    root.mainloop()