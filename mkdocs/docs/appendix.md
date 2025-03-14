## Appendix

### How to install Python

Download and install Python from [https://www.python.org/](https://www.python.org/)

Start the installation, set checkboxes, customize installation, restart the system to make sure that the path information are in affect.

<table>
    <tr>
        <td>
            <img src='./images/python_install1.png'>
        </td>
        <td>
            <img src='./images/python_install2.png'>
        </td>
        <td>
            <img src='./images/python_install3.png'>
        </td>
    </tr>
</table>

### Headless mode

To run the script with headless mode, use the following command:

```sh
python src/main.py [project_path] [options]
```

### Arguments

- `project_path`: Path to the Automation Studio project file (.apj).

### Options

- `--headless`: Run in headless mode without GUI.
- `--debug_level`: Set the debug level (integer).
- `--separate_update_files`: Separate update files into a different zip. Can be specified as `true` or `false`. 
- `--include_runtime_updates`: Include runtime updates. Can be specified as `true` or `false`. 
- `--include_technology_updates`: Include technology updates. Can be specified as `true` or `false`. 
- `--include_hardware_updates`: Include hardware updates. Can be specified as `true` or `false`. 
- `--include_as_updates`: Include Automation Studio updates. Can be specified as `true` or `false`. 
- `--include_binary_folder`: Include binary folder. Can be specified as `true` or `false`. 
- `--include_diag_folder`: Include diagnosis folder. Can be specified as `true` or `false`. 
- `--include_temp_folder`: Include temp folder. Can be specified as `true` or `false`. 
- `--include_dot_folder`: Include dot folders. Can be specified as `true` or `false`. 

If an option is not specified, the value from config.ini will be used.

### Examples

#### Run with GUI

```sh
python src/main.py "C:\\projects\\sps_sample\\sample.apj"
```

#### Run in Headless Mode

```sh
python src/main.py "C:\\projects\\sps_sample\\sample.apj" --headless
```

#### Include Binary Folder and Technology Updates

```sh
python src/main.py "C:\\projects\\sps_sample\\sample.apj" --include_binary_folder --include_technology_updates
```

#### Set Debug Level and Separate Update Files

```sh
python src/main.py "C:\\projects\\sps_sample\\sample.apj" --debug_level 3 --separate_update_files
```

## Notes

- If a switch is specified without `true` or `false`, it is considered `True`.
- If a switch is specified as `false`, it is considered `False`.
- If a switch is not specified, it is considered `None`.