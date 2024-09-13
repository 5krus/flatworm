import tkinter as tk
from tkinter import filedialog
import json

def open_config_window(config):
    def save_config():
        repo_path = repo_path_entry.get()
        branch = branch_entry.get()
        exclude = exclude_entry.get().split(',')
        config['repo_path'] = repo_path
        config['branch'] = branch
        config['exclude_patterns'] = exclude
        with open('config/config.json', 'w') as config_file:
            json.dump(config, config_file)
        config_window.destroy()

    config_window = tk.Tk()
    config_window.title("Configuration")

    tk.Label(config_window, text="Repository Path:").grid(row=0)
    repo_path_entry = tk.Entry(config_window)
    repo_path_entry.grid(row=0, column=1)
    tk.Button(config_window, text="Browse", command=lambda: repo_path_entry.insert(0, filedialog.askdirectory())).grid(row=0, column=2)

    tk.Label(config_window, text="Branch:").grid(row=1)
    branch_entry = tk.Entry(config_window)
    branch_entry.grid(row=1, column=1)

    tk.Label(config_window, text="Exclude Patterns (comma-separated):").grid(row=2)
    exclude_entry = tk.Entry(config_window)
    exclude_entry.grid(row=2, column=1)

    tk.Button(config_window, text="Save", command=save_config).grid(row=3, column=1)
    config_window.mainloop()