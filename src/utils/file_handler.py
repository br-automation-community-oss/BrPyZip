import chardet
import re
import os
import configparser
import xml.etree.ElementTree as ET
import glob
import zipfile

# Process all files
def process_files(file_path, hmi_instance):
    try:
        # Create main zip file
        main_file = updates_file = os.path.dirname(file_path) + ".zip"
        create_zip_file(updates_file, hmi_instance)
        if hmi_instance.separate_update_files_var.get():
            updates_file = os.path.dirname(file_path) + "_Updates.zip"
            create_zip_file(updates_file, hmi_instance)
            
        # Process project apj file, this are mapp components
        hmi_instance.progress['value'] = 10
        hmi_instance.master.update()
        content = open_file(file_path, hmi_instance)
        as_version, result = tech_file_handling(updates_file, hmi_instance, content)
        if not result or hmi_instance.cancelled:
            return
        
        # Process the CPU file, this are the runtime files
        if hmi_instance.include_runtime_updates_var.get():
            hmi_instance.progress['value'] = 30
            hmi_instance.master.update()
            result = cpu_file_handling(file_path, updates_file, as_version, hmi_instance)
            if not result or hmi_instance.cancelled:
                return

        # Process the HW file, this are the firmware files
        if hmi_instance.include_hardware_updates_var.get():
            hmi_instance.progress['value'] = 50
            hmi_instance.master.update()
            result = hw_file_handling(file_path, updates_file, as_version, hmi_instance)
            if not result or hmi_instance.cancelled:
                return

        # Process project files
        hmi_instance.progress['value'] = 70
        hmi_instance.master.update()
        project_file_handling(main_file, hmi_instance)

        hmi_instance.create_log(f"--------------------------------------------------------------------------------------------------------------------------------------------")
        hmi_instance.create_log(f"Finished")
        hmi_instance.progress['value'] = 100

    except Exception as e:
        hmi_instance.create_error(f"An error occurred: {e}")

# Process project files
def project_file_handling(main_file, hmi_instance):
    try:
        hmi_instance.create_log(f"--------------------------------------------------------------------------------------------------------------------------------------------")
        hmi_instance.create_log(f"Add project files")

        with zipfile.ZipFile(main_file, 'a', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(main_file.replace('.zip', '')):
                if hmi_instance.cancelled:
                    hmi_instance.create_log(f"Cancelled") 
                    return False
                
                if not hmi_instance.include_binary_var.get() and 'Binaries' in dirs:
                    dirs.remove('Binaries')  # Ignore the Binaries directory
                    if hmi_instance.DEBUG_LEVEL > 1:
                        hmi_instance.create_log(f"Removed binaries folder")        
                if not hmi_instance.include_diagnostic_var.get() and 'Diagnosis' in dirs:
                    dirs.remove('Diagnosis')  # Ignore the Binaries directory           
                    if hmi_instance.DEBUG_LEVEL > 1:
                        hmi_instance.create_log(f"Removed diagnosis folder")        
                if not hmi_instance.include_temp_var.get() and 'Temp' in dirs:
                    dirs.remove('Temp')  # Ignore the Binaries directory           
                    if hmi_instance.DEBUG_LEVEL > 1:
                        hmi_instance.create_log(f"Removed temp folder")        
                for file in files:
                    if hmi_instance.cancelled:
                        hmi_instance.create_log(f"Cancelled") 
                        return
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, main_file.replace('.zip', ''))
                    zipf.write(file_path, arcname)
                    if hmi_instance.DEBUG_LEVEL > 1:
                        hmi_instance.create_log(f"Added {file_path}")

    except Exception as e:
        hmi_instance.create_error(f"Failed to process project files: {e}")

# Process PLC hardware files
def hw_file_handling(file_path, updates_file, as_version, hmi_instance):
    hmi_instance.create_log(f"--------------------------------------------------------------------------------------------------------------------------------------------")
    hmi_instance.create_log(f"Add hardware files")

    try:
        # Read the configuration file
        config = configparser.ConfigParser()
        config.read("config.ini")
        if config.has_option('AS', as_version):
            config_as_path = config.get('AS', as_version)
        else:
            hmi_instance.create_error(f"The configuration for '{as_version}' does not exist. Check configuration file and make sure an entry for AS version {as_version} exists.")
            return as_version, False
        
        config_as_data = config.get('AS', 'Data')

        physical_path = os.path.dirname(file_path) + '/Physical'
        if not os.path.exists(physical_path):
            hmi_instance.create_error("Can not find the physical folder")
            return False

        # get all configurations
        for dir_name in os.listdir(physical_path):
            if hmi_instance.cancelled:
                hmi_instance.create_log(f"Cancelled") 
                return False

            folder_path = os.path.join(physical_path, dir_name)
            if os.path.isdir(folder_path):
                if hmi_instance.DEBUG_LEVEL > 0:
                    hmi_instance.create_log(f"Found config folder {folder_path}")

                # -----------------------------------------------------------------------------------------------------------------------
                # Read external hardware details
                for dir_name_plc in os.listdir(folder_path):
                    folder_path_ext = os.path.join(folder_path, dir_name_plc)
                    if os.path.isdir(folder_path_ext):
                        if hmi_instance.DEBUG_LEVEL > 1:
                            hmi_instance.create_log(f"Found PLC folder {folder_path_ext}")

                        if os.path.exists(folder_path_ext + "/ExternalHardware"):
                            if hmi_instance.DEBUG_LEVEL > 0:
                                hmi_instance.create_log(f"Found external hardware folder in {folder_path_ext}")

                                content = open_file(folder_path_ext + "/" + "/ExternalHardware/ExternalHardwareDevices.xml", hmi_instance)
                                
                                # Load and parse the XML file
                                tree = ET.ElementTree(ET.fromstring(content))
                                root = tree.getroot()

                                # Iterate through all Module elements                               
                                for module in root.findall('.//Module'):
                                    if hmi_instance.cancelled:
                                        hmi_instance.create_log(f"Cancelled") 
                                        return False

                                    module_id = module.get('ModuleID')
                                    module_version = module.get('Version')
                                    source_file = module.find('SourceFile')
                                    original_file = source_file.get('OriginalFile') if source_file is not None else 'N/A'

                                    if hmi_instance.DEBUG_LEVEL > 0:
                                        hmi_instance.create_log(f'Found external module {module_id}, original file name {original_file}')

                                    firmware_path = config_as_data + '/AS' + as_version.replace('_', '') + "/Hardware/Modules" + f"/{module_id}" + f"/{module_version}/Source"
                                    if os.path.exists(firmware_path):
                                        # Find the exact file name using glob
                                        search_pattern = firmware_path + f"/{original_file}"
                                        matching_files = glob.glob(search_pattern)
                                        
                                        if matching_files:
                                            file_name = matching_files[0]  # Take the first match
                                            if hmi_instance.DEBUG_LEVEL > 0:
                                                hmi_instance.create_log(f"Add external firmware file {file_name}")

                                            add_zip_file([file_name], updates_file, 'AS\ExternalHardware\Modules' + f"/{module_id}", hmi_instance)

                                        elif hmi_instance.DEBUG_LEVEL > 1:
                                            hmi_instance.create_log(f"No external firmware file found for {module_type} and {module_version}")

                # -----------------------------------------------------------------------------------------------------------------------
                # Read common hardware details
                content = open_file(folder_path + "/" + "/Hardware.hw", hmi_instance)

                # Placeholder for file handling logic
                tree = ET.ElementTree(ET.fromstring(content))
                root = tree.getroot()

                namespace = {'ns': 'http://br-automation.co.at/AS/Hardware'}
                modules = root.findall('.//ns:Module', namespace)
                
                for module in modules:
                    if hmi_instance.cancelled:
                        hmi_instance.create_log(f"Cancelled") 
                        return False

                    module_type = module.get('Type')
                    module_version = module.get('Version')
                    if hmi_instance.DEBUG_LEVEL > 1:
                        hmi_instance.create_log(f'Found module type {module_type} with version {module_version}')

                    if os.path.exists(config_as_path +  "/Upgrades" + f"/{module_type}"):
                        if os.path.exists(config_as_path +  "/Upgrades" + f"/{module_type}" + f"/{module_version}"):
                    
                            # Find the exact file name using glob
                            search_pattern = config_as_path +  "/Upgrades" + f"/{module_type}" + f"/{module_version}" + f"/*.exe"
                            matching_files = glob.glob(search_pattern)
                            if matching_files:
                                file_name = matching_files[0]  # Take the first match
                                if hmi_instance.DEBUG_LEVEL > 0:
                                    hmi_instance.create_log(f"Add firmware file {file_name}")
                                add_zip_file([file_name], updates_file, 'Upgrades', hmi_instance)
                            elif hmi_instance.DEBUG_LEVEL > 1:
                                hmi_instance.create_log(f"No firmware file found for {module_type} and {module_version}")
        return True
    except Exception as e:
        hmi_instance.create_error(f"Failed to process hardware files: {e}")    

# Process PLC runtime files
def cpu_file_handling(file_path, updates_file, as_version, hmi_instance):
    hmi_instance.create_log(f"--------------------------------------------------------------------------------------------------------------------------------------------")
    hmi_instance.create_log(f"Add runtime files")

    try:
        # Read the configuration file
        config = configparser.ConfigParser()
        config.read("config.ini")

        if config.has_option('AS', as_version):
            config_as_path = config.get('AS', as_version)
        else:
            hmi_instance.create_error(f"The configuration for '{as_version}' does not exist. Check configuration file and make sure an entry for AS version {as_version} exists.")
            return as_version, False

        if config.has_option('AS', as_version + '_base'):
            config_base_path = config.get('AS', as_version + '_base')
        else:
            hmi_instance.create_error(f"The configuration for '{as_version}_base')' does not exist. Check configuration file and make sure an entry for AS version {as_version}_base') exists.")
            return as_version, False
    
        if 'TRANSLATE' in config:
            translate_dict = dict(config.items('TRANSLATE'))
            translate_dict = {key.upper(): value.upper() for key, value in translate_dict.items()}

        physical_path = os.path.dirname(file_path) + '/Physical'
        if not os.path.exists(physical_path):
            hmi_instance.create_error("Can not find the physical folder")
            return False

        # get all configurations
        for dir_name in os.listdir(physical_path):
            if hmi_instance.cancelled:
                hmi_instance.create_log(f"Cancelled") 
                return False

            folder_path = os.path.join(physical_path, dir_name)
            if os.path.isdir(folder_path):
                if hmi_instance.DEBUG_LEVEL > 1:
                    hmi_instance.create_log(f"Found config folder {folder_path}")

                folders = [name for name in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, name))]
                if folders:
                    content = open_file(folder_path + "/" + folders[0] + "/Cpu.pkg", hmi_instance)

                    module_id = re.search(r'Configuration ModuleId="([^"]+)"', content)
                    if module_id:
                        cpu_type = module_id.group(1)
                        if hmi_instance.DEBUG_LEVEL > 1:
                            hmi_instance.create_log(f"CPU type is {cpu_type}")

                        # Check if any entry from TRANSLATE is in cpu_type
                        for key, value in translate_dict.items():
                            pattern = re.compile(key)
                            if pattern.match(cpu_type):
                                cpu_type = value
                                if hmi_instance.DEBUG_LEVEL > 1:
                                    hmi_instance.create_log(f"Found substitute CPU type is {cpu_type}")

                        # Get the runtime version
                        runtime_version = re.search(r'AutomationRuntime Version="([^"]+)"', content)
                        if runtime_version:
                            parts = runtime_version.group(1).split('.')
                            major_version = parts[0][1:].zfill(2)
                            runtime_version = f'M{major_version}{parts[1]}'
                            if hmi_instance.DEBUG_LEVEL > 1:
                                hmi_instance.create_log(f"Runtime version is {runtime_version}")

                            # Find the exact file name using glob
                            search_pattern = os.path.join(config_base_path, "Upgrades", f"*AR_{runtime_version}_{cpu_type}*.exe")
                            matching_files = glob.glob(search_pattern)
                            if matching_files:
                                file_name = matching_files[0]  # Take the first match
                                if hmi_instance.DEBUG_LEVEL > 0:
                                    hmi_instance.create_log(f"Add runtime file {file_name}")
                                add_zip_file([file_name], updates_file, 'Upgrades', hmi_instance)
                            elif hmi_instance.DEBUG_LEVEL > 1:
                                hmi_instance.create_log(f"No runtime file found for {runtime_version} and {cpu_type}")

                        if hmi_instance.cancelled:
                            hmi_instance.create_log(f"Cancelled") 
                            return False
                        
                        # Get the vc version
                        vc_version = re.search(r'Vc FirmwareVersion="([^"]+)"', content)
                        if vc_version:
                            vc_version = vc_version.group(1)
                            hmi_instance.create_log(f"VC version is {vc_version}")

                            # Find the exact file name using glob
                            search_pattern = os.path.join(config_as_path, "Upgrades", f"*VC_{vc_version}*.exe")
                            matching_files = glob.glob(search_pattern)
                            if matching_files:
                                file_name = matching_files[0]  # Take the first match
                                if hmi_instance.DEBUG_LEVEL > 0:
                                    hmi_instance.create_log(f"Add VC file {file_name}")
                                add_zip_file([file_name], updates_file, 'Upgrades', hmi_instance)    
                            elif hmi_instance.DEBUG_LEVEL > 1:
                                hmi_instance.create_log(f"No VC file found for {vc_version}")
        return True                                   
           
    except Exception as e:
        hmi_instance.create_error(f"Failed to process runtime files: {e}")

# Process project apj file
def tech_file_handling(updates_file, hmi_instance, content):
    hmi_instance.create_log(f"--------------------------------------------------------------------------------------------------------------------------------------------")
    hmi_instance.create_log(f"Find AS version")

    try:
        # Read the configuration file
        config = configparser.ConfigParser()
        config.read("config.ini")
        
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
            if hmi_instance.DEBUG_LEVEL > 0:
                hmi_instance.create_log(f"AS version is {as_version}")
    
            if config.has_option('AS', as_version):
                config_as_path = config.get('AS', as_version)
                if hmi_instance.DEBUG_LEVEL > 0:
                    hmi_instance.create_log(f"AS path {config_as_path}")
                if not os.path.exists(config_as_path):
                    hmi_instance.create_error(f"The path '{config_as_path}' does not exist. Check configuration file and make sure an entry for AS version {as_version} is correct.")
                    return as_version, False
            else:
                hmi_instance.create_error(f"The configuration for '{as_version}' does not exist. Check configuration file and make sure an entry for AS version {as_version} exists.")
                return as_version, False
        else:
            hmi_instance.create_error("No AS version found in the APJ file")
            return None, False

        # Finish here when technology updates are disabled
        if not hmi_instance.include_technology_updates_var.get():
            return as_version, True

        # Find the TechnologyPackages element with the namespace
        hmi_instance.create_log(f"Add technology files")
        technology_packages_element = root.find('ns:TechnologyPackages', namespace)
        if technology_packages_element is None:
            hmi_instance.create_log("WARNING: No Technology Packages element not found in the XML file")

        technology_packages = []
        for package in technology_packages_element:
            if hmi_instance.cancelled:
                hmi_instance.create_log(f"Cancelled") 
                return False

            name = package.tag.split('}')[1] 
            version = package.attrib.get('Version')

            # Ignore elements with the name 'mapp'
            if name.lower() == 'mapp':
                continue
                
            if hmi_instance.DEBUG_LEVEL > 0:
                hmi_instance.create_log(f"Found technology package {name} version {version}")

            # Find the exact file name using glob            
            search_pattern = os.path.join(config_as_path, "Upgrades", "AS" + as_version[0:1] + f"_TP_{name}_{version}*.exe")
            matching_files = glob.glob(search_pattern)
            if matching_files:
                file_name = matching_files[0]  # Take the first match
                if hmi_instance.DEBUG_LEVEL > 1:
                    hmi_instance.create_log(f"Add technology file {file_name}")
                add_zip_file([file_name], updates_file, 'Upgrades', hmi_instance)
            elif hmi_instance.DEBUG_LEVEL > 0:
                hmi_instance.create_log(f"WARNING: No file found for technology package {name} version {version}")

        return as_version, True
    except Exception as e:
        hmi_instance.create_error(f"Failed to handle APJ file: {e}")

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
        hmi_instance.create_error(f"Failed to open file '{file_path}': {e}")

# Create a zip file
def create_zip_file(zip_file_name, hmi_instance):
    try:
        with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if not hmi_instance.separate_update_files_var.get():
                zipf.writestr('Upgrades/', '')  # Create an empty directory named 'upgrades'
    except Exception as e:
        hmi_instance.create_error(f"Failed to create zip file '{zip_file_name}': {e}")

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
        hmi_instance.create_error(f"Failed to add file to zip '{zip_file_name}': {e}")                    