## Introduction

Python script to zip B&R Automation Studio projects including all updates.

![](./images/overview.png)

The script will zip the project and all updates in the project. The zip file will be saved in the same folder as the project.

## Running the script

The script can be run in two ways:

### All in one executable

1. Download the latest release from the [releases page](https://github.com/br-automation-com/BrPyZip/releases)
2. Run the executable

### Python script

1. Download the source code from the [releases page]
2. Install the required packages 'pip install -r requirements.txt'
3. Run the script with python './src/main.py'

## Configuration

The script can be configured using the `config.ini` file. The config has 3 sections:

### AS

The `AS` section contains the path to the Automation Studio installation. This is used to find the `Update` folder. Make sure the path in this section matches your Automation Studio installations.

### GENERAL

In the general section you can set the debug level. The debug level can be set to 0 = errors, 1 = info, 2 = debug. The other options in this section are the last settings from the UI.

### TRANSLATE

Some CPUs share the same runtime file. For example, the X20CP3687 and X20CP1687 share the same runtime file. The `TRANSLATE` section is used to translate the CPU name to the runtime file.


