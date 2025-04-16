import tkinter as tk
from tkinter import scrolledtext, font, simpledialog, messagebox
import re

class MarkdownViewerApp:
    """
    Tkinter application for displaying Markdown text in a basic way
    and allowing validation or sending a remark.
    """
    def __init__(self, root, markdown_text, agent_name = "Agent"):
        """
        Initialize the application.

        Args:
            root: The main Tkinter window (tk.Tk()).
            markdown_text: The string containing the Markdown text.
        """
        self.root = root
        self.markdown_text = markdown_text
        self.remark_sent = None

        self.root.title("Markdown Viewer and Validation")
        self.root.geometry("1400x800")

        self.root.grid_rowconfigure(0, weight=0, minsize=30)
        self.root.grid_rowconfigure(1, weight=8, minsize=500)
        self.root.grid_rowconfigure(2, weight=0, minsize=30)
        self.root.grid_rowconfigure(3, weight=2, minsize=150)
        self.root.grid_rowconfigure(4, weight=0, minsize=50)
        self.root.grid_columnconfigure(0, weight=1)

        text_main_frame = tk.Frame(root, height=500)
        text_main_frame.grid(row=1, column=0, sticky="nsew")
        text_main_frame.pack_propagate(False)
        text_main_frame.grid_propagate(False)

        text_remark_frame = tk.Frame(root, height=150)
        text_remark_frame.grid(row=3, column=0, sticky="nsew")
        text_remark_frame.pack_propagate(False)
        text_remark_frame.grid_propagate(False)

        self.md_label = tk.Label(
            root, 
            text=f"Markdown Text from {agent_name}:", 
            anchor="w",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0",
            padx=5,
            pady=3
        )
        self.md_label.grid(row=0, column=0, sticky="ew", padx=10, pady=(5, 0))

        self.text_widget = scrolledtext.ScrolledText(
            text_main_frame,
            wrap=tk.WORD,
            padx=10,
            pady=10,
            relief=tk.FLAT
        )
        self.text_widget.pack(fill="both", expand=True)

        self.remark_label = tk.Label(
            root, 
            text="Add your remark below (optional):", 
            anchor="w",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0",
            padx=5,
            pady=3
        )
        self.remark_label.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 0))
        
        self.text_remark = scrolledtext.ScrolledText(
            text_remark_frame,
            wrap=tk.WORD,
            padx=10,
            pady=10,
            relief=tk.FLAT
        )
        self.text_remark.pack(fill="both", expand=True)

        # Configure fonts and tags for formatting
        self.configure_tags()

        # Display Markdown content
        self.display_markdown(self.markdown_text)

        # Make the text area non-editable by the user
        self.text_widget.config(state=tk.DISABLED)

        button_frame = tk.Frame(root, pady=10)
        button_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=10)

        self.save_button = tk.Button(
            button_frame,
            text="Save",
            command=self.save_text,
            width=20
        )
        self.save_button.pack(side=tk.TOP, pady=10)

    def configure_tags(self):
        """Configure Tkinter tags to simulate Markdown formatting."""
        default_font = font.nametofont("TkDefaultFont")
        default_family = default_font.actual("family")
        default_size = default_font.actual("size")

        code_font = font.Font(family="Courier New", size=default_size)

        bold_font = font.Font(family=default_family, size=default_size, weight="bold")
        self.text_widget.tag_configure("bold", font=bold_font)

        italic_font = font.Font(family=default_family, size=default_size, slant="italic")
        self.text_widget.tag_configure("italic", font=italic_font)

        self.text_widget.tag_configure("code", font=code_font, background="#f0f0f0")

        h1_font = font.Font(family=default_family, size=int(default_size * 1.5), weight="bold")
        h2_font = font.Font(family=default_family, size=int(default_size * 1.2), weight="bold")
        h3_font = font.Font(family=default_family, size=int(default_size * 1.1), weight="bold")
        self.text_widget.tag_configure("h1", font=h1_font, spacing3=10)
        self.text_widget.tag_configure("h2", font=h2_font, spacing3=8)
        self.text_widget.tag_configure("h3", font=h3_font, spacing3=6)
        self.text_widget.tag_configure("list_item", lmargin1=20, lmargin2=20)


    def display_markdown(self, md_text):
        """
        Display Markdown text in the Text widget with basic formatting.
        NOTE: This is a very simplified interpretation of Markdown.
        """
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete("1.0", tk.END)

        lines = md_text.strip().split('\n')
        for line in lines:
            stripped_line = line.strip()
            current_line_start = self.text_widget.index(tk.INSERT)

            is_formatted = False
            if stripped_line.startswith("# "):
                self.text_widget.insert(tk.INSERT, stripped_line[2:] + "\n", "h1")
                is_formatted = True
            elif stripped_line.startswith("## "):
                self.text_widget.insert(tk.INSERT, stripped_line[3:] + "\n", "h2")
                is_formatted = True
            elif stripped_line.startswith("### "):
                self.text_widget.insert(tk.INSERT, stripped_line[4:] + "\n", "h3")
                is_formatted = True
            elif stripped_line.startswith("* ") or stripped_line.startswith("- "):
                self.text_widget.insert(tk.INSERT, line + "\n", "list_item")
                is_formatted = True
            # Add other rules here (e.g., ``` for code blocks)

            if not is_formatted:
                 self.text_widget.insert(tk.INSERT, line + "\n")

            current_line_end = self.text_widget.index(f"{current_line_start} + {len(line)} chars")
            self.apply_inline_formatting(current_line_start, current_line_end)

        content = self.text_widget.get("1.0", tk.END)
        if content.endswith("\n\n"):
             self.text_widget.delete(f"{tk.END}-2c", f"{tk.END}-1c")

        self.text_widget.config(state=tk.DISABLED)


    def apply_inline_formatting(self, start_index, end_index):
        """
        Apply 'bold', 'italic', 'code' tags on a text range
        using regular expressions.
        """
        content = self.text_widget.get(start_index, end_index)

        def apply_tag_around_markers(pattern, tag_name):
            for match in re.finditer(pattern, content, re.DOTALL):
                match_start_abs = self.text_widget.index(f"{start_index} + {match.start()} chars")
                match_end_abs = self.text_widget.index(f"{start_index} + {match.end()} chars")
                self.text_widget.tag_add(tag_name, match_start_abs, match_end_abs)

        apply_tag_around_markers(r"`(.+?)`", "code")

        apply_tag_around_markers(r"(?:\*\*|__)(.+?)(?:\*\*|__)", "bold")

        apply_tag_around_markers(r"(?<![\*_])(?:\*|_)(.+?)(?:\*|_)(?![\*_])", "italic")


    def save_text(self):
        """Action when the 'Save' button is clicked."""
        remark_text = self.text_remark.get("1.0", tk.END).strip()
        if remark_text:
            self.remark_sent = remark_text
            print(f"Action: Remark saved: '{self.remark_sent}'")
        else:
            print("Action: No remark provided")
        
        self.root.destroy()

if __name__ == "__main__":
    markdown_input = r"""
    # Main Document Title

    This is an introduction paragraph. It contains normal text.
    We can include **bold text** or __also bold text__.

    We can also have *italic text* or _like this_.

    ## Important Subtitle

    Here is a list of items:
    * First item with `inline code`.
    * Second item.
    * Third item with **bold** and *italic* combined (the rendering may be simple).

    Some `inline code` in a normal sentence.

    Be careful with special characters like \* or \_ which shouldn't be formatted.

    """
    main_window = tk.Tk()

    app = MarkdownViewerApp(main_window, markdown_input, "MyAgent 1")

    main_window.mainloop()

    if app.remark_sent is not None:
        print(f"\nPost-closure processing: A remark was saved: '{app.remark_sent}'")
    else:
        print("\nPost-closure processing: No remark was provided.")