import os
import fnmatch
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from datetime import datetime

LOG_FILE_PREFIX = "app_log"
LOG_FILE_EXTENSION = ".txt"
LOG_FILE_SIZE_LIMIT = 100 * 1024 * 1024  # 100MB
TEMP_PATHS_FILE = "tempPaths.txt"

stop_event = threading.Event()

def list_folders(path):
    try:
        folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
        return folders
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def list_files_in_folders(path):
    try:
        write_log(f"Processing path: {path}")
        if not os.path.exists(path):
            write_log(f"Path does not exist: {path}")
            return {}
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        write_log(f"Files in path {path}: {files}")
        return {path: files}
    except Exception as e:
        write_log(f"An error occurred while listing files: {e}")
        return {}

def get_log_file():
    index = 0
    while True:
        log_file = f"{LOG_FILE_PREFIX}_{index}{LOG_FILE_EXTENSION}"
        if not os.path.exists(log_file) or os.path.getsize(log_file) < LOG_FILE_SIZE_LIMIT:
            return log_file
        index += 1

def write_log(message):
    log_file = get_log_file()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"{timestamp} - {message}\n")

def search_words_in_files(path, words, patterns, output_file, progress_callback, total_matches_callback):
    try:
        files_in_folders = list_files_in_folders(path)
        write_log(f"Files in folders: {files_in_folders}")
        matching_lines = []
        total_folders = len(files_in_folders)
        current_folder_index = 0
        total_matches = 0  # Initialize total matches counter
        for folder, files in files_in_folders.items():
            if stop_event.is_set():
                write_log("Search stopped by user.")
                break
            current_folder_index += 1
            progress_callback(f"Listing files in folder: {folder} ({current_folder_index}/{total_folders})")
            total_files = len(files)
            for file_index, file in enumerate(files, start=1):
                if stop_event.is_set():
                    write_log("Search stopped by user.")
                    break
                progress_callback(f"Searching in file: {file} ({file_index}/{total_files})")
                # Debug logging for pattern matching
                write_log(f"Checking file: {file} against patterns: {patterns}")
                if any(fnmatch.fnmatch(file, pattern.strip()) for pattern in patterns):
                    file_path = os.path.join(path, file)
                    write_log(f"Processing file: {file_path}")
                    try:
                        with open(file_path, 'r') as f:
                            lines = f.readlines()
                            for line in lines:
                                if stop_event.is_set():
                                    write_log("Search stopped by user.")
                                    break
                                if any(word in line for word in words):
                                    file_name_parts = file.split('_')
                                    datetime_str = file_name_parts[0]
                                    datetime_formatted = f"{datetime_str[:4]}-{datetime_str[4:6]}-{datetime_str[6:8]} {datetime_str[8:10]}:{datetime_str[10:12]}:{datetime_str[12:14]}.{datetime_str[14:]}"
                                    serial_number = '_'.join(file_name_parts[1:-1])
                                    number_machine = file_name_parts[-1].split(".")[0]
                                    formatted_result = f'"{file}","{datetime_formatted}","{serial_number}","{number_machine}",{line.strip()}'
                                    matching_lines.append(formatted_result)
                                    total_matches += 1  # Increment total matches counter
                                    #write_log(f"Found matching line: {formatted_result}")
                                    total_matches_callback(total_matches)  # Update total matches count on UI
                    except Exception as e:
                        write_log(f"Error processing file {file_path}: {e}")
        
        with open(output_file, 'a') as out_f:
            for line in matching_lines:
                out_f.write(line + '\n')
                
        progress_callback(f"Search completed. Total matches found: {total_matches}")
        return matching_lines
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def browse_folder():
    folder_selected = filedialog.askdirectory()
    folder_path.set(folder_selected)

def update_progress(message):
    progress_label.config(text=message)
    write_log(message)
    app.update_idletasks()

def update_total_matches(total_matches):
    total_matches_label.config(text=f"Total matches found: {total_matches}")
    app.update_idletasks()

def start_search():
    start_button.config(state=tk.DISABLED)
    folder_entry.config(state=tk.DISABLED)
    words_entry.config(state=tk.DISABLED)
    patterns_entry.config(state=tk.DISABLED)
    output_file_entry.config(state=tk.DISABLED)
    progress_label.config(text="App started. Running search...")
    total_matches_label.config(text="Total matches found: 0")
    path = folder_path.get()
    words = words_entry.get().split(',')
    patterns = [pattern.strip() for pattern in patterns_entry.get().split(',')]
    output_file = output_file_entry.get()
    if not path or not words or not patterns or not output_file:
        messagebox.showerror("Error", "All fields are required")
        start_button.config(state=tk.NORMAL)
        folder_entry.config(state=tk.NORMAL)
        words_entry.config(state=tk.NORMAL)
        patterns_entry.config(state=tk.NORMAL)
        output_file_entry.config(state=tk.NORMAL)
        return
    if os.path.exists(output_file):
        overwrite = messagebox.askyesno("Overwrite File", f"The file {output_file} already exists. Do you want to overwrite it?")
        if not overwrite:
            start_button.config(state=tk.NORMAL)
            folder_entry.config(state=tk.NORMAL)
            words_entry.config(state=tk.NORMAL)
            patterns_entry.config(state=tk.NORMAL)
            output_file_entry.config(state=tk.NORMAL)
            return
    with open(TEMP_PATHS_FILE, 'w') as f:
        for folder in list_folders(path):
            f.write(os.path.join(path, folder).replace("\\", "/") + '\n')
    search_thread = threading.Thread(target=run_search, args=(words, patterns, output_file))
    search_thread.start()

def run_search(words, patterns, output_file):
    while os.path.exists(TEMP_PATHS_FILE) and not stop_event.is_set():
        with open(TEMP_PATHS_FILE, 'r') as f:
            paths = f.readlines()
        if not paths:
            os.remove(TEMP_PATHS_FILE)
            break
        current_path = paths[0].strip()
        update_progress(f"Searching in folder: {current_path}")
        search_words_in_files(current_path.replace("/", "\\"), words, patterns, output_file, update_progress, update_total_matches)
        with open(TEMP_PATHS_FILE, 'w') as f:
            f.writelines(paths[1:])
    progress_label.config(text="Search completed.")
    start_button.config(state=tk.NORMAL)
    folder_entry.config(state=tk.NORMAL)
    words_entry.config(state=tk.NORMAL)
    patterns_entry.config(state=tk.NORMAL)
    output_file_entry.config(state=tk.NORMAL)

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        stop_event.set()
        app.destroy()

app = tk.Tk()
app.title("Fuji Search Files")
app.protocol("WM_DELETE_WINDOW", on_closing)

folder_path = tk.StringVar()

tk.Label(app, text="Folder Path:").grid(row=0, column=0, padx=10, pady=10)
folder_entry = tk.Entry(app, textvariable=folder_path, width=50)
folder_entry.grid(row=0, column=1, padx=10, pady=10)
tk.Button(app, text="Browse", command=browse_folder).grid(row=0, column=2, padx=10, pady=10)

tk.Label(app, text="Words (comma separated):").grid(row=1, column=0, padx=10, pady=10)
words_entry = tk.Entry(app, width=50)
words_entry.grid(row=1, column=1, padx=10, pady=10)

tk.Label(app, text="Patterns (comma separated):").grid(row=2, column=0, padx=10, pady=10)
patterns_entry = tk.Entry(app, width=50)
patterns_entry.grid(row=2, column=1, padx=10, pady=10)

tk.Label(app, text="Output File:").grid(row=3, column=0, padx=10, pady=10)
output_file_entry = tk.Entry(app, width=50)
output_file_entry.grid(row=3, column=1, padx=10, pady=10)

start_button = tk.Button(app, text="Start Search", command=start_search)
start_button.grid(row=4, column=0, columnspan=3, pady=20)

progress_label = tk.Label(app, text="")
progress_label.grid(row=5, column=0, columnspan=3, pady=10)

total_matches_label = tk.Label(app, text="Total matches found: 0")
total_matches_label.grid(row=6, column=0, columnspan=3, pady=10)

app.mainloop()
