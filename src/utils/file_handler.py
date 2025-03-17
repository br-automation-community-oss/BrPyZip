import chardet
import re
import os
import sys
import xml.etree.ElementTree as ET
import glob
import zipfile
from tkinter import messagebox
from datetime import datetime

def update_progress(hmi_instance, value):
    if hmi_instance:
        hmi_instance.progress['value'] = value
        hmi_instance.master.update()

# Process all files
def process_files(config, file_path, hmi_instance=None):
    try:
        # If project_path is a directory, find the .apj file
        if os.path.isdir(file_path):
            apj_files = [f for f in os.listdir(file_path) if f.endswith('.apj')]
            if not apj_files:
                create_error(f"No .apj file found in the specified directory '{file_path}'", hmi_instance)
                sys.exit(0)
            file_path = os.path.join(file_path, apj_files[0])

        # Create main zip file
        main_file = updates_file = os.path.dirname(file_path) + ".zip"
        create_zip_file(updates_file, config.getboolean('GENERAL', 'separate_update_files', fallback=False), hmi_instance)
        if config.getboolean('GENERAL', 'separate_update_files', fallback=False):
            updates_file = os.path.dirname(file_path) + "_Updates.zip"
            create_zip_file(updates_file, config.getboolean('GENERAL', 'separate_update_files', fallback=False), hmi_instance)
            
        # Process project apj file, this are mapp components
        update_progress(hmi_instance, 10)
        content = open_file(file_path, hmi_instance)
        as_version, result = tech_file_handling(config, updates_file, hmi_instance, content)
        if not result or (hmi_instance and hmi_instance.cancelled):
            return
        
        # Process the CPU file, this are the runtime files
        if config.getboolean('GENERAL', 'include_runtime_updates', fallback=True):
            update_progress(hmi_instance, 30)
            result = cpu_file_handling(config, file_path, updates_file, as_version, hmi_instance)
            if not result or (hmi_instance and hmi_instance.cancelled):
                return

        # Process the HW file, this are the firmware files
        if config.getboolean('GENERAL', 'include_hardware_updates', fallback=True):
            update_progress(hmi_instance, 50)
            result = hw_file_handling(config, file_path, updates_file, as_version, hmi_instance)
            if not result or (hmi_instance and hmi_instance.cancelled):
                return

        # Process project files
        update_progress(hmi_instance, 70)
        project_file_handling(config, main_file, hmi_instance)

        create_log(f"--------------------------------------------------------------------------------------------------------------------------------------------", hmi_instance)
        create_log(f"Finished", hmi_instance)
        update_progress(hmi_instance, 100)

    except Exception as e:
        create_error(f"An error occurred: {e}", hmi_instance)

# Process project files
def project_file_handling(config, main_file, hmi_instance):
    create_log(f"--------------------------------------------------------------------------------------------------------------------------------------------", hmi_instance)
    create_log(f"Add project files", hmi_instance)

    try:

        DEBUG_LEVEL = int(config.get('GENERAL', 'debug_level'))
        INCLUDE_BINARY = config.getboolean('GENERAL', 'include_binary_folder', fallback=False)
        INCLUDE_DIAG = config.getboolean('GENERAL', 'include_diag_folder', fallback=False)
        INCLUDE_TEMP = config.getboolean('GENERAL', 'include_temp_folder', fallback=False)
        INCLUDE_DOT = config.getboolean('GENERAL', 'include_dot', fallback=False)

        with zipfile.ZipFile(main_file, 'a', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(main_file.replace('.zip', '')):
                if hmi_instance and hmi_instance.cancelled:
                    create_log(f"Cancelled", hmi_instance)
                    return False
                
                dot_folders = [d for d in dirs if d.startswith('.')]
                if dot_folders:
                    if not INCLUDE_DOT:
                        if DEBUG_LEVEL > 1:
                            create_log(f"Removed dot folders: {dot_folders}", hmi_instance)

                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                if not INCLUDE_BINARY and 'Binaries' in dirs:
                    dirs.remove('Binaries')  # Ignore the Binaries directory
                    if DEBUG_LEVEL > 1:
                        create_log(f"Removed binaries folder", hmi_instance)        
                if not INCLUDE_DIAG and 'Diagnosis' in dirs:
                    dirs.remove('Diagnosis')  # Ignore the diagnosis directory           
                    if DEBUG_LEVEL > 1:
                        create_log(f"Removed diagnosis folder", hmi_instance)        
                if not INCLUDE_TEMP and 'Temp' in dirs:
                    dirs.remove('Temp')  # Ignore the temp directory           
                    if DEBUG_LEVEL > 1:
                        create_log(f"Removed temp folder", hmi_instance)              
                for file in files:
                    if hmi_instance and hmi_instance.cancelled:
                        create_log(f"Cancelled", hmi_instance) 
                        return
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, main_file.replace('.zip', ''))
                    zipf.write(file_path, arcname)
                    if DEBUG_LEVEL > 1:
                        create_log(f"Added {file_path}", hmi_instance)

    except Exception as e:
        create_error(f"Failed to process project files: {e}", hmi_instance)

# Process PLC hardware files
def hw_file_handling(config, file_path, updates_file, as_version, hmi_instance):
    create_log(f"--------------------------------------------------------------------------------------------------------------------------------------------", hmi_instance)
    create_log(f"Add hardware files", hmi_instance)

    try:
        # Read the configuration file
        DEBUG_LEVEL = int(config.get('GENERAL', 'debug_level'))
        if config.has_option('AS', as_version):
            config_as_path = config.get('AS', as_version)
        else:
            create_error(f"The configuration for '{as_version}' does not exist. Check configuration file and make sure an entry for AS version {as_version} exists.", hmi_instance)
            return as_version, False
        
        config_as_data = config.get('AS', 'Data')

        physical_path = os.path.dirname(file_path) + '/Physical'
        if not os.path.exists(physical_path):
            create_error("Can not find the physical folder", hmi_instance)
            return False

        # get all configurations
        for dir_name in os.listdir(physical_path):
            if hmi_instance and hmi_instance.cancelled:
                create_log(f"Cancelled", hmi_instance) 
                return False

            folder_path = os.path.join(physical_path, dir_name)
            if os.path.isdir(folder_path):
                if DEBUG_LEVEL > 0:
                    create_log(f"Found config folder {folder_path}", hmi_instance)

                # -----------------------------------------------------------------------------------------------------------------------
                # Read external hardware details
                for dir_name_plc in os.listdir(folder_path):
                    folder_path_ext = os.path.join(folder_path, dir_name_plc)
                    if os.path.isdir(folder_path_ext):
                        if DEBUG_LEVEL > 1:
                            create_log(f"Found PLC folder {folder_path_ext}", hmi_instance)

                        if os.path.exists(folder_path_ext + "/ExternalHardware"):
                            if DEBUG_LEVEL > 0:
                                create_log(f"Found external hardware folder in {folder_path_ext}", hmi_instance)

                                ExternalHardwareFile = folder_path_ext + "/" + "/ExternalHardware/ExternalHardwareDevices.xml"
                                if os.path.exists(ExternalHardwareFile):
                                    content = open_file(ExternalHardwareFile, hmi_instance)
                                    
                                    # Load and parse the XML file
                                    tree = ET.ElementTree(ET.fromstring(content))
                                    root = tree.getroot()

                                    # Iterate through all Module elements                               
                                    for module in root.findall('.//Module'):
                                        if hmi_instance and hmi_instance.cancelled:
                                            create_log(f"Cancelled", hmi_instance) 
                                            return False

                                        module_id = module.get('ModuleID')
                                        module_version = module.get('Version')
                                        source_file = module.find('SourceFile')
                                        original_file = source_file.get('OriginalFile') if source_file is not None else 'N/A'

                                        if DEBUG_LEVEL > 0:
                                            create_log(f'Found external module {module_id}, original file name {original_file}', hmi_instance)

                                        firmware_path = config_as_data + '/AS' + as_version.replace('_', '') + "/Hardware/Modules" + f"/{module_id}" + f"/{module_version}/Source"
                                        if os.path.exists(firmware_path):
                                            # Find the exact file name using glob
                                            search_pattern = firmware_path + f"/{original_file}"
                                            matching_files = glob.glob(search_pattern)

                                            if matching_files:
                                                file_name = matching_files[0]  # Take the first match
                                                if DEBUG_LEVEL > 0:
                                                    create_log(f"Add external firmware file {file_name}", hmi_instance)

                                                add_zip_file([file_name], updates_file, 'AS/ExternalHardware/Modules' + f"/{module_id}", hmi_instance)

                                            elif DEBUG_LEVEL > 1:
                                                create_log(f"No external firmware file found for {module_type} and {module_version}", hmi_instance)
                                elif DEBUG_LEVEL > 0:
                                    create_log(f"Found external hardware folder but no ExternalHardwareDevices.xml file in {folder_path_ext}", hmi_instance)

                # -----------------------------------------------------------------------------------------------------------------------
                # Read common hardware details
                hardware_file = folder_path + "/" + "/Hardware.hw"
                if not os.path.exists(hardware_file):
                    create_log(f"Can not find the hardware file in {folder_path}", hmi_instance)

                else:
                    content = open_file(folder_path + "/" + "/Hardware.hw", hmi_instance)

                    # Placeholder for file handling logic
                    tree = ET.ElementTree(ET.fromstring(content))
                    root = tree.getroot()

                    namespace = {'ns': 'http://br-automation.co.at/AS/Hardware'}
                    modules = root.findall('.//ns:Module', namespace)
                    
                    for module in modules:
                        if hmi_instance and hmi_instance.cancelled:
                            create_log(f"Cancelled", hmi_instance) 
                            return False

                        module_type = module.get('Type')
                        module_version = module.get('Version')
                        if DEBUG_LEVEL > 1:
                            create_log(f'Found module type {module_type} with version {module_version}', hmi_instance)

                        if os.path.exists(config_as_path +  "/Upgrades" + f"/{module_type}"):
                            if os.path.exists(config_as_path +  "/Upgrades" + f"/{module_type}" + f"/{module_version}"):
                        
                                # Find the exact file name using glob
                                search_pattern = config_as_path +  "/Upgrades" + f"/{module_type}" + f"/{module_version}" + f"/*.exe"
                                matching_files = glob.glob(search_pattern)
                                if matching_files:
                                    file_name = matching_files[0]  # Take the first match
                                    if DEBUG_LEVEL > 0:
                                        create_log(f"Add firmware file {file_name}", hmi_instance)
                                    add_zip_file([file_name], updates_file, 'Upgrades', hmi_instance)
                                elif DEBUG_LEVEL > 1:
                                    create_log(f"No firmware file found for {module_type} and {module_version}", hmi_instance)
        return True
    except Exception as e:
        create_error(f"Failed to process hardware files: {e}", hmi_instance)    

# Process PLC runtime files
def cpu_file_handling(config, file_path, updates_file, as_version, hmi_instance):
    create_log(f"--------------------------------------------------------------------------------------------------------------------------------------------", hmi_instance)
    create_log(f"Add runtime files", hmi_instance)

    try:
        # Read the configuration file
        DEBUG_LEVEL = int(config.get('GENERAL', 'debug_level'))

        if config.has_option('AS', as_version):
            config_as_path = config.get('AS', as_version)
        else:
            create_error(f"The configuration for '{as_version}' does not exist. Check configuration file and make sure an entry for AS version {as_version} exists.", hmi_instance)
            return as_version, False

        if config.has_option('AS', as_version + '_base'):
            config_base_path = config.get('AS', as_version + '_base')
        else:
            create_error(f"The configuration for '{as_version}_base')' does not exist. Check configuration file and make sure an entry for AS version {as_version}_base') exists.", hmi_instance)
            return as_version, False
    
        if 'TRANSLATE' in config:
            translate_dict = dict(config.items('TRANSLATE'))
            translate_dict = {key.upper(): value.upper() for key, value in translate_dict.items()}

        physical_path = os.path.dirname(file_path) + '/Physical'
        if not os.path.exists(physical_path):
            create_error("Can not find the physical folder", hmi_instance)
            return False

        # get all configurations
        for dir_name in os.listdir(physical_path):
            if hmi_instance and hmi_instance.cancelled:
                create_log(f"Cancelled", hmi_instance) 
                return False

            folder_path = os.path.join(physical_path, dir_name)
            if os.path.isdir(folder_path):
                if DEBUG_LEVEL > 1:
                    create_log(f"Found config folder {folder_path}", hmi_instance)

                folders = [name for name in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, name))]
                if folders:
                    content = open_file(folder_path + "/" + folders[0] + "/Cpu.pkg", hmi_instance)

                    module_id = re.search(r'Configuration ModuleId="([^"]+)"', content)
                    if module_id:
                        cpu_type = module_id.group(1)
                        if DEBUG_LEVEL > 1:
                            create_log(f"CPU type is {cpu_type}", hmi_instance)

                        # Check if any entry from TRANSLATE is in cpu_type
                        for key, value in translate_dict.items():
                            pattern = re.compile(key)
                            if pattern.match(cpu_type):
                                cpu_type = value
                                if DEBUG_LEVEL > 1:
                                    create_log(f"Found substitute CPU type is {cpu_type}", hmi_instance)

                        # Get the runtime version
                        runtime_version = re.search(r'AutomationRuntime Version="([^"]+)"', content)
                        if runtime_version:
                            parts = runtime_version.group(1).split('.')
                            major_version = parts[0][1:].zfill(2)
                            runtime_version = f'M{major_version}{parts[1]}'
                            if DEBUG_LEVEL > 1:
                                create_log(f"Runtime version is {runtime_version}", hmi_instance)

                            # Find the exact file name using glob
                            search_pattern = os.path.join(config_base_path, "Upgrades", f"*AR_{runtime_version}_{cpu_type}*.exe")
                            matching_files = glob.glob(search_pattern)
                            if matching_files:
                                file_name = matching_files[0]  # Take the first match
                                if DEBUG_LEVEL > 0:
                                    create_log(f"Add runtime file {file_name}", hmi_instance)
                                add_zip_file([file_name], updates_file, 'Upgrades', hmi_instance)
                            elif DEBUG_LEVEL > 1:
                                create_log(f"No runtime file found for {runtime_version} and {cpu_type}", hmi_instance)

                        if hmi_instance and hmi_instance.cancelled:
                            create_log(f"Cancelled", hmi_instance) 
                            return False
                        
                        # Get the vc version
                        vc_version = re.search(r'Vc FirmwareVersion="([^"]+)"', content)
                        if vc_version:
                            vc_version = vc_version.group(1)
                            create_log(f"VC version is {vc_version}", hmi_instance)

                            # Find the exact file name using glob
                            search_pattern = os.path.join(config_as_path, "Upgrades", f"*VC_{vc_version}*.exe")
                            matching_files = glob.glob(search_pattern)
                            if matching_files:
                                file_name = matching_files[0]  # Take the first match
                                if DEBUG_LEVEL > 0:
                                    create_log(f"Add VC file {file_name}", hmi_instance)
                                add_zip_file([file_name], updates_file, 'Upgrades', hmi_instance)    
                            elif DEBUG_LEVEL > 1:
                                create_log(f"No VC file found for {vc_version}", hmi_instance)
        return True                                   
           
    except Exception as e:
        create_error(f"Failed to process runtime files: {e}", hmi_instance)

# Process project apj file
def tech_file_handling(config, updates_file, hmi_instance, content):
    create_log(f"--------------------------------------------------------------------------------------------------------------------------------------------", hmi_instance)
    create_log(f"Find AS version", hmi_instance)

    try:
        # Read the configuration file
        DEBUG_LEVEL = int(config.get('GENERAL', 'debug_level'))
        INCLUDE_AS_UPDATES = config.getboolean('GENERAL', 'include_as_updates', fallback=False)
        INCLUDE_TECHNOLOGY_UPDATES = config.getboolean('GENERAL', 'include_technology_updates', fallback=True)
        
        # Define the namespace
        namespace = {'ns': 'http://br-automation.co.at/AS/Project'}

        # Placeholder for file handling logic
        tree = ET.ElementTree(ET.fromstring(content))
        root = tree.getroot()

        # Find AS version
        working_version = re.search(r'AutomationStudio Version="([^"]+)"', content)
        if working_version:
            as_version = working_version.group(1)
            parts = as_version.split('.')
            if len(parts) > 2:
                as_version = '.'.join(parts[:2]).replace('.', '_')
            if DEBUG_LEVEL > 0:
                create_log(f"AS version is {as_version}", hmi_instance)
    
            if config.has_option('AS', as_version):
                config_as_path = config.get('AS', as_version)
                if DEBUG_LEVEL > 0:
                    create_log(f"AS path {config_as_path}", hmi_instance)
                if not os.path.exists(config_as_path):
                    create_error(f"The path '{config_as_path}' does not exist. Check configuration file and make sure an entry for AS version {as_version} is correct.", hmi_instance)
                    return as_version, False
            else:
                create_error(f"The configuration for '{as_version}' does not exist. Check configuration file and make sure an entry for AS version {as_version} exists.", hmi_instance)
                return as_version, False
        else:
            create_error("No AS version found in the APJ file", hmi_instance)
            return None, False

        # Include automation studio update files
        if INCLUDE_AS_UPDATES:
            sp_version = working_version.group(1)
            if "SP" in sp_version:
                sp_version = sp_version.replace(" SP", "_SP")
                if DEBUG_LEVEL > 1:
                    create_log(f"AS is using service pack {sp_version}", hmi_instance)

                search_pattern = os.path.join(config_as_path, "Upgrades", "AS" + as_version[0:1] + f"_AS_{sp_version}*.exe")
                matching_files = glob.glob(search_pattern)
                if matching_files:
                    file_name = matching_files[0]  # Take the first match
                    if DEBUG_LEVEL > 1:
                        create_log(f"Add service pack file {file_name}", hmi_instance)
                    add_zip_file([file_name], updates_file, 'Upgrades', hmi_instance)
                elif DEBUG_LEVEL > 0:
                    create_log(f"WARNING: No file found for service pack version {sp_version}", hmi_instance)

        if hmi_instance and hmi_instance.cancelled:
            create_log(f"Cancelled", hmi_instance) 
            return False
            
        # Finish here when technology updates are disabled
        if not INCLUDE_TECHNOLOGY_UPDATES:
            return as_version, True

        # Find the TechnologyPackages element with the namespace
        create_log(f"Add technology files", hmi_instance)
        technology_packages_element = root.find('ns:TechnologyPackages', namespace)
        if technology_packages_element is None:
            create_log("No Technology Packages element not found in the XML file", hmi_instance)

        else:
            technology_packages = []
            for package in technology_packages_element:
                if hmi_instance and hmi_instance.cancelled:
                    create_log(f"Cancelled", hmi_instance) 
                    return False

                name = package.tag.split('}')[1] 
                version = package.attrib.get('Version')

                # Ignore elements with the name 'mapp'
                if name.lower() == 'mapp':
                    name = 'mappServices'
                    
                if DEBUG_LEVEL > 0:
                    create_log(f"Found technology package {name} version {version}", hmi_instance)

                # Find the exact file name using glob            
                search_pattern = os.path.join(config_as_path, "Upgrades", "AS" + as_version[0:1] + f"_TP_{name}_{version}*.exe")
                matching_files = glob.glob(search_pattern)
                if matching_files:
                    file_name = matching_files[0]  # Take the first match
                    if DEBUG_LEVEL > 1:
                        create_log(f"Add technology file {file_name}", hmi_instance)
                    add_zip_file([file_name], updates_file, 'Upgrades', hmi_instance)
                elif DEBUG_LEVEL > 0:
                    create_log(f"WARNING: No file found for technology package {name} version {version}", hmi_instance)

        return as_version, True
    except Exception as e:
        create_error(f"Failed to handle APJ file: {e}", hmi_instance)

# Generic open file function
def open_file(file_path, hmi_instance):
    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
        
        with open(file_path, 'r', encoding=encoding) as file:
            content = file.read()
        return content.replace('\n', '')
    except Exception as e:
        create_error(f"Failed to open file '{file_path}': {e}", hmi_instance)

# Create a zip file
def create_zip_file(zip_file_name, SEPARATE_UPDATE_FILES, hmi_instance):
    try:
        with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if not SEPARATE_UPDATE_FILES:
                zipf.writestr('Upgrades/', '')  # Create an empty directory named 'upgrades'
    except Exception as e:
        create_error(f"Failed to create zip file '{zip_file_name}': {e}", hmi_instance)

# Add files to a zip file
def add_zip_file(file_paths, zip_file_name, zip_path, hmi_instance):
    try:
        with zipfile.ZipFile(zip_file_name, 'a', zipfile.ZIP_DEFLATED) as zipf:
            existing_files = set(zipf.namelist())
            for file_path in file_paths:
                arcname = f'{zip_path}/{os.path.basename(file_path)}'
                if arcname not in existing_files:
                    zipf.write(file_path, arcname)
    except Exception as e:
        create_error(f"Failed to add file to zip '{zip_file_name}': {e}", hmi_instance) 

# Create log messages entries
def create_log(log_text, hmi_instance=None):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{current_time} - {log_text}"

    if hmi_instance:
        hmi_instance.log_text.configure(state="normal")  # Enable editing temporarily
        hmi_instance.log_text.insert("end", log_entry + "\n")    # Insert the new log entry
        hmi_instance.log_text.configure(state="disabled") # Disable editing again
        hmi_instance.log_text.see("end") # Autoscroll to the end
        
        # Refresh the window
        hmi_instance.master.update()
    else:
        print(log_entry)

# Create error messages entries
def create_error(error_text, hmi_instance=None):
    """
    Creates a popup with the provided error text.

    Args:
        error_text (str): The error text to be displayed.

    Returns:
        None
    """
    if hmi_instance:
        create_log(f"ERROR: {error_text}")
        messagebox.showerror("Error", error_text)
    else:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{current_time} - {error_text}\n"
        print(log_entry)
