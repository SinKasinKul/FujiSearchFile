import os
import fnmatch

def list_folders(path):
    try:
        # List all directories in the given path
        folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
        return folders
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def list_files_in_folders(path):
    try:
        # List all directories in the given path
        folders = list_folders(path)
        files_in_folders = {}
        for folder in folders:
            folder_path = os.path.join(path, folder)
            files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            files_in_folders[folder] = files
        return files_in_folders
    except Exception as e:
        print(f"An error occurred: {e}")
        return {}

def search_words_in_files(path, words, patterns, output_file):
    try:
        files_in_folders = list_files_in_folders(path)
        matching_lines = []
        for folder, files in files_in_folders.items():
            for file in files:
                if any(fnmatch.fnmatch(file, pattern) for pattern in patterns):
                    file_path = os.path.join(path, folder, file)
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                        for line in lines:
                            if any(word in line for word in words):
                                file_name_parts = file.split('_')
                                if len(file_name_parts) == 4:
                                    serial_number = f"{file_name_parts[1]}_{file_name_parts[2]}"
                                    number_machine = file_name_parts[3].split(".")[0]
                                elif len(file_name_parts) == 5:
                                    serial_number = f"{file_name_parts[1]}_{file_name_parts[2]}_{file_name_parts[3]}"
                                    number_machine = file_name_parts[4].split(".")[0]
                                formatted_result = f'"{serial_number}","{number_machine}",{line.strip()}'
                                matching_lines.append(formatted_result)
        
        with open(output_file, 'w') as out_f:
            for line in matching_lines:
                out_f.write(line + '\n')
                
        return matching_lines
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

# Example usage
path = 'E:\\LogFuji\\BackUp'
words = ['1362-00394', '1190160']
patterns = ['*NXTIIIc17.DAT', '*NXTIIIc18.DAT']
output_file = 'FujiSearch.txt'
folders = list_folders(path)
# print(folders)

files_in_folders = list_files_in_folders(path)
# print(files_in_folders)

matching_lines = search_words_in_files(path, words, patterns, output_file)
for line in matching_lines:
    print(line)