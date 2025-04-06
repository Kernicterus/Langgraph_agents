import tkinter as tk
from tkinter import filedialog, Text, Label
import os

def get_files_and_context(dir_path=None):
    """
    Open a tkinter window to get the UI files of the webapp, context and architecture requirements.
    
    Args:
        dir_path (str, optional): Path to directory. If None, opens file dialog.
        
    Returns:
        tuple: (list of files, project context string, architecture requirements string)
    """
    try:
        root = tk.Tk()
        root.title("Project Selection")
        
        dir_frame = tk.Frame(root)
        dir_frame.pack(pady=10, padx=10, fill=tk.X)
        
        dir_label = Label(dir_frame, text="Markdown mockups folder:")
        dir_label.pack(side=tk.LEFT)
        
        dir_path_var = tk.StringVar()
        dir_entry = tk.Entry(dir_frame, textvariable=dir_path_var, width=50)
        dir_entry.pack(side=tk.LEFT, padx=5)
        
        def choose_directory():
            selected_dir = filedialog.askdirectory(
                title="Select folder containing files",
                mustexist=True
            )
            if selected_dir:
                dir_path_var.set(selected_dir)
                
        browse_button = tk.Button(dir_frame, text="Browse", command=choose_directory)
        browse_button.pack(side=tk.LEFT)
        
        context_frame = tk.Frame(root)
        context_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        context_label = Label(context_frame, text="Web project context:")
        context_label.pack()
        
        context_text = Text(context_frame, height=10, width=50)
        context_text.pack(pady=5)

        architecture_frame = tk.Frame(root)
        architecture_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        architecture_label = Label(architecture_frame, text="Architecture requirements:")
        architecture_label.pack()
        
        architecture_text = Text(architecture_frame, height=10, width=50)
        architecture_text.pack(pady=5)
        
        result = {"dir_path": "", "context": "", "architecture": ""}
        
        def save_and_close():
            result["dir_path"] = dir_path_var.get()
            result["context"] = context_text.get("1.0", "end-1c")
            result["architecture"] = architecture_text.get("1.0", "end-1c")
            root.destroy()
            
        save_button = tk.Button(root, text="Validate", command=save_and_close)
        save_button.pack(pady=10)
        
        if dir_path:
            dir_path_var.set(dir_path)
            
        root.mainloop()
        
        if not result["dir_path"]:
            print("No folder selected")
            return [], "", ""
            
        files = []
        for file in os.listdir(result["dir_path"]):
            if file.endswith(('.md', '.txt')):
                with open(os.path.join(result["dir_path"], file), 'r', encoding='utf-8') as f:
                    files.append({
                        'name': file,
                        'content': f.read()
                    })
        return files, result["context"], result["architecture"]
        
    except Exception as e:
        print(f"Error retrieving files: {e}")
        return [], "", ""
