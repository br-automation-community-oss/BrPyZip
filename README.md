# Human-Machine Interface (HMI) Application

This project is a simple Human-Machine Interface (HMI) application developed using Tkinter. The application features a user interface with a button that allows users to open and select files.

## Project Structure

```
hmi-app
├── src
│   ├── main.py          # Entry point of the application
│   ├── ui
│   │   └── hmi.py      # Contains the HMI class for the user interface
│   └── utils
│       └── file_handler.py # Utility functions for file operations
├── requirements.txt     # Lists the project dependencies
└── README.md            # Documentation for the project
```

## Requirements

To run this application, you need to install the following dependencies:

- Tkinter (usually included with Python installations)
- Any other libraries specified in `requirements.txt`

## Installation

1. Clone the repository or download the project files.
2. Navigate to the project directory.
3. Install the required dependencies by running:

```
pip install -r requirements.txt
```

## Running the Application

To start the application, run the following command:

```
python src/main.py
```

This will open the Tkinter window with the HMI interface. Click the button to open a file dialog and select a file.

## License

This project is open-source and available under the MIT License.