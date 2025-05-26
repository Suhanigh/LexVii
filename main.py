import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from editor import CodeEditor
from lexer import Lexer
from dfa_visualizer import DFAVisualizer
from localization import Localization
from themes import VS_CODE_DARK
import traceback
import tempfile
import subprocess
import re
from typing import List

class LexViApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LexVi - Lexical Analysis Learning Tool")
        self.root.geometry("1200x800")
        self.root.configure(bg=VS_CODE_DARK['background'])
        
        # Initialize localization
        self.localization = Localization()
        
        # Create top bar (like VS Code)
        self.create_top_bar()
        
        # Create main layout
        self.create_layout()
        
        # Initialize components
        self.init_components()
        
        # Status bar
        self.status_bar = tk.Label(
            self.root, text="Ready", anchor=tk.W,
            bg=VS_CODE_DARK['status_bar_bg'], fg=VS_CODE_DARK['status_bar_fg']
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Configure grid weights for responsive layout
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

    def create_top_bar(self):
        """Create the top bar with language selector and run button."""
        self.top_bar = ttk.Frame(self.root, height=32)
        self.top_bar.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)
        
        # App name
        app_name = ttk.Label(
            self.top_bar,
            text=self.localization.get_text("app_name"),
            font=("Segoe UI", 12, "bold"),
            background=VS_CODE_DARK['menu_bg'],
            foreground=VS_CODE_DARK['accent']
        )
        app_name.pack(side=tk.LEFT, padx=(8, 5), pady=0)
        
        # Language label
        lang_label = ttk.Label(self.top_bar, text="Language:",
                               background=VS_CODE_DARK['menu_bg'],
                               foreground=VS_CODE_DARK['menu_fg'])
        lang_label.pack(side=tk.LEFT, padx=(10, 2), pady=0)
        
        # Language selector
        self.lang_var = tk.StringVar(value="python")
        lang_combo = ttk.Combobox(
            self.top_bar,
            textvariable=self.lang_var,
            values=["python", "cpp", "java"],
            state="readonly",
            width=10,
            font=("Segoe UI", 10)
        )
        lang_combo.pack(side=tk.LEFT, padx=(0, 5), pady=0)
        lang_combo.bind("<<ComboboxSelected>>", self._on_language_change)
        
        # Run button
        # Use a consistent style for the run button
        style = ttk.Style()
        style.configure('Run.TButton', background=VS_CODE_DARK['accent'], foreground=VS_CODE_DARK['status_bar_fg'],
                        font=("Segoe UI", 11, "bold"), borderwidth=0)
        style.map('Run.TButton', background=[('active', VS_CODE_DARK['highlight'])])
        
        run_btn = ttk.Button(
            self.top_bar,
            text=self.localization.get_text("run"),
            command=self.run_code,
            style='Run.TButton'
        )
        run_btn.pack(side=tk.RIGHT, padx=8, pady=2)

        # Add Lexer menu
        lexer_menu = tk.Menu(self.root, tearoff=0, bg=VS_CODE_DARK['menu_bg'], fg=VS_CODE_DARK['menu_fg'])
        lexer_menu.add_command(label="Import Rules...", command=self._import_lexer_rules)
        
        # Add Lexer menu button
        lexer_menu_btn = ttk.Menubutton(self.top_bar, text="Lexer")
        lexer_menu_btn['menu'] = lexer_menu
        lexer_menu_btn.pack(side=tk.LEFT, padx=5)

    def create_layout(self):
        # Main horizontal layout: sidebar + main content
        self.main_frame = tk.Frame(self.root, bg=VS_CODE_DARK['background'])
        self.main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        # Sidebar (like VS Code)
        self.sidebar = tk.Frame(self.main_frame, width=48, bg=VS_CODE_DARK['sidebar_bg'])
        self.sidebar.grid(row=0, column=0, sticky="ns")
        
        # Sidebar icons with tooltips (Ensure icons are packed with padding)
        icons = [
            ("Editor", self.localization.get_text('sidebar.editor')),
            ("Search", self.localization.get_text('sidebar.explorer')),
            ("Settings", self.localization.get_text('sidebar.settings'))
        ]
        
        for icon, tooltip in icons:
            btn = tk.Label(
                self.sidebar, text=icon, bg=VS_CODE_DARK['sidebar_bg'], 
                fg=VS_CODE_DARK['sidebar_fg'], font=("Segoe UI", 11)
            )
            btn.pack(pady=8)
            self._create_tooltip(btn, tooltip)

        # Main content area (horizontal split)
        self.content_paned = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.content_paned.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)

        # Left pane: Code Editor and Output (vertical split)
        self.left_pane = ttk.PanedWindow(self.content_paned, orient=tk.VERTICAL)
        self.content_paned.add(self.left_pane, weight=2)
        
        # Frame for editor
        self.editor_frame = tk.Frame(self.left_pane, bg=VS_CODE_DARK['background'])
        self.left_pane.add(self.editor_frame, weight=3)
        
        # Frame for output
        self.output_frame = tk.Frame(self.left_pane, bg=VS_CODE_DARK['background'])
        self.left_pane.add(self.output_frame, weight=1)
        
        # Set initial sash position for left pane (adjust as needed for better initial view)
        self.left_pane.sashpos(0, 400)

        # Right pane: Tabs (Token Analysis, Code Execution) and DFA Visualizer (vertical split)
        self.right_pane = ttk.PanedWindow(self.content_paned, orient=tk.VERTICAL)
        self.content_paned.add(self.right_pane, weight=2)
        
        # Set initial sash position for main horizontal pane (adjust as needed)
        self.content_paned.sashpos(0, 700)
        
        # Notebook for tabs (ensure background is set via style if needed)
        style = ttk.Style()
        style.configure('TNotebook', background=VS_CODE_DARK['background'], borderwidth=0)
        style.configure('TNotebook.Tab', background=VS_CODE_DARK['sidebar_bg'], foreground=VS_CODE_DARK['sidebar_fg'], padding=[10, 5])
        style.map('TNotebook.Tab', background=[('selected', VS_CODE_DARK['highlight'])], foreground=[('selected', VS_CODE_DARK['foreground'])])

        self.right_tabs = ttk.Notebook(self.right_pane, style='TNotebook')
        self.right_pane.add(self.right_tabs, weight=1)
        
        # Tab for Token Analysis
        self.token_analysis_frame = tk.Frame(self.right_tabs, bg=VS_CODE_DARK['background'])
        self.right_tabs.add(self.token_analysis_frame, text=self.localization.get_text('sidebar.token_analysis', 'Token Analysis'))
        
        # Tab for Code Execution Output
        self.code_execution_frame = tk.Frame(self.right_tabs, bg=VS_CODE_DARK['background'])
        self.right_tabs.add(self.code_execution_frame, text=self.localization.get_text('sidebar.code_execution', 'Code Execution'))
        
        # Frame for DFA Visualizer (ensure padding)
        self.dfa_frame = tk.Frame(self.right_pane, bg=VS_CODE_DARK['background'])
        self.right_pane.add(self.dfa_frame, weight=1)
        
        # Set initial sash position for right pane (adjust as needed)
        self.right_pane.sashpos(0, 300)

    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(
                tooltip, text=text, justify=tk.LEFT,
                background=VS_CODE_DARK['highlight'], foreground=VS_CODE_DARK['foreground'],
                relief=tk.SOLID, borderwidth=1, font=("Segoe UI", 10)
            )
            label.pack()
            
            def hide_tooltip():
                tooltip.destroy()
            
            widget.tooltip = tooltip
            widget.bind('<Leave>', lambda e: hide_tooltip())
        
        widget.bind('<Enter>', show_tooltip)

    def init_components(self):
        # Initialize code editor
        self.editor = CodeEditor(self.editor_frame, theme=VS_CODE_DARK)
        self.editor.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Initialize output text widget (ensure theme is applied and packing is correct)
        self.output_text = tk.Text(
            self.output_frame, # Pack output_text into output_frame
            bg=VS_CODE_DARK['editor_bg'],
            fg=VS_CODE_DARK['editor_fg'],
            insertbackground=VS_CODE_DARK['editor_cursor'],
            selectbackground=VS_CODE_DARK['editor_selection'],
            font=('Consolas', 11),
            wrap=tk.WORD,
            state=tk.DISABLED # Start in disabled state
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Initialize token table (ensure parent frame is correct and packing is correct)
        self.create_token_table(self.token_analysis_frame)
        
        # Initialize DFA visualizer (Pass editor instance)
        self.dfa_visualizer = DFAVisualizer(self.dfa_frame, theme=VS_CODE_DARK, editor=self.editor)
        self.dfa_visualizer.pack(fill=tk.BOTH, expand=True)
        
        # Initialize lexer
        self.lexer = Lexer()
        self.tokens: List[Token] = [] # Store tokens here
        
        # Bind editor changes to lexer
        self.editor.bind("<<TextChanged>>", self.on_editor_change)
        
        # Set initial focus to the editor
        self.editor.focus_set()

    def create_token_table(self, parent_frame):
        columns = (
            self.localization.get_text('token_table.lexeme'),
            self.localization.get_text('token_table.token'),
            self.localization.get_text('token_table.line'),
            self.localization.get_text('token_table.column')
        )
        
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Treeview",
                        background=VS_CODE_DARK['token_table_bg'],
                        foreground=VS_CODE_DARK['token_table_fg'],
                        fieldbackground=VS_CODE_DARK['token_table_bg'],
                        borderwidth=0,
                        font=("Consolas", 11))
        style.configure("Treeview.Heading",
                        background=VS_CODE_DARK['token_table_header_bg'],
                        foreground=VS_CODE_DARK['token_table_header_fg'],
                        font=("Segoe UI", 10, "bold"))
        
        self.token_table = ttk.Treeview(parent_frame, columns=columns, show="headings", style="Treeview")
        for col in columns:
            self.token_table.heading(col, text=col)
            self.token_table.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.token_table.yview)
        self.token_table.configure(yscrollcommand=scrollbar.set)
        
        self.token_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=2)

    def on_editor_change(self, event=None):
        print("on_editor_change called") # Debug print
        text = self.editor.get("1.0", tk.END).strip()
        if not text:
            self.tokens = [] # Clear tokens
            self.update_token_table([])
            self.dfa_visualizer.update_dfa([])
            return
            
        self.tokens = self.lexer.tokenize(text) # Store tokens
        print(f"Generated {len(self.tokens)} tokens") # Debug print: number of tokens
        self.update_token_table(self.tokens)
        self.dfa_visualizer.update_dfa(self.tokens) # Pass tokens to DFA visualizer
        
        # Set the animation sequence for the DFA visualizer
        self.dfa_visualizer.animation_sequence = [token.value for token in self.tokens]

    def update_token_table(self, tokens):
        for item in self.token_table.get_children():
            self.token_table.delete(item)
        for token in tokens:
            self.token_table.insert("", tk.END, values=(
                token.value,
                token.type,
                token.line,
                token.column
            ))

    # VS Code-style menu popups
    def show_file_menu(self):
        self._show_menu([(self.localization.get_text('new_file', 'New'), self.new_file),
                         (self.localization.get_text('open_file', 'Open'), self.open_file),
                         (self.localization.get_text('save_file', 'Save'), self.save_file),
                         ('-', None),
                         (self.localization.get_text('exit', 'Exit'), self.root.quit)])
    def show_edit_menu(self):
        self._show_menu([(self.localization.get_text('undo', 'Undo'), self.undo),
                         (self.localization.get_text('redo', 'Redo'), self.redo)])
    def show_view_menu(self):
        self._show_menu([(self.localization.get_text('zoom_in', 'Zoom In'), self.zoom_in),
                         (self.localization.get_text('zoom_out', 'Zoom Out'), self.zoom_out)])
    def show_language_menu(self):
        langs = self.localization.get_available_languages()
        self._show_menu([(lang, lambda l=lang: self.change_language(l)) for lang in langs])
    def show_help_menu(self):
        self._show_menu([(self.localization.get_text('about', 'About'), self.show_about)])

    def _show_menu(self, items):
        menu = tk.Menu(self.root, tearoff=0, bg=VS_CODE_DARK['menu_bg'], fg=VS_CODE_DARK['menu_fg'],
                       activebackground=VS_CODE_DARK['highlight'], activeforeground=VS_CODE_DARK['accent'])
        for label, cmd in items:
            if label == '-':
                menu.add_separator()
            else:
                menu.add_command(label=label, command=cmd)
        try:
            x = self.root.winfo_pointerx() - self.root.winfo_rootx()
            y = self.root.winfo_pointery() - self.root.winfo_rooty() + 32
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def new_file(self):
        self.editor.delete("1.0", tk.END)
    def open_file(self):
        pass
    def save_file(self):
        pass
    def undo(self):
        self.editor.undo()
    def redo(self):
        self.editor.redo()
    def zoom_in(self):
        self.editor.zoom_in()
    def zoom_out(self):
        self.editor.zoom_out()
    def change_language(self, language):
        self.localization.set_language(language)
        self.update_ui_language()
    def update_ui_language(self):
        """Update all UI elements with new language."""
        # Update window title
        self.root.title(self.localization.get_text('app_title'))
        
        # Update status bar
        self.status_bar.config(text=self.localization.get_text('ready'))
        
        # Update token table headers
        columns = (
            self.localization.get_text('token_table.lexeme'),
            self.localization.get_text('token_table.token'),
            self.localization.get_text('token_table.line'),
            self.localization.get_text('token_table.column')
        )
        for i, col in enumerate(columns):
            self.token_table.heading(f"#{i+1}", text=col)
        
        # Update DFA controls
        self.dfa_visualizer.update_controls_text(
            step_text=self.localization.get_text('step'),
            reset_text=self.localization.get_text('reset'),
            export_text=self.localization.get_text('export')
        )
    def show_about(self):
        messagebox.showinfo(
            "About LexVi",
            "LexVi - Smart Learning Tool for Lexical Analysis and DFA\n"
            "Version 1.0\n\n"
            "A tool designed to help students learn lexical analysis concepts."
        )

    def _on_language_change(self, event=None):
        """Handle language selection change."""
        language = self.lang_var.get()
        self.editor.set_language(language)
        self._update_status(f"Language changed to {language}")

    def run_code(self):
        print("run_code called") # Debug print
        """Run the code in the editor."""
        code = self.editor.get("1.0", tk.END).strip()
        if not code:
            print("Editor is empty, not running code.") # Debug print
            return
        
        language = self.lang_var.get()
        
        # Select the Code Execution tab
        self.right_tabs.select(self.code_execution_frame)
        
        # Clear previous output and enable writing
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        
        try:
            if language == "python":
                self._run_python(code)
            elif language in ["cpp", "c"]:
                self._run_c_cpp(code, language)
            elif language == "java":
                self._run_java(code)
        except Exception as e:
            self._show_error(str(e))
        finally:
            # Disable writing after execution
            self.output_text.config(state=tk.DISABLED)

    def _run_python(self, code):
        """Run Python code."""
        import sys
        from io import StringIO
        
        # Redirect stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout = StringIO()
        stderr = StringIO()
        sys.stdout = stdout
        sys.stderr = stderr
        
        try:
            # Execute the code
            exec(code)
            
            # Get output
            output = stdout.getvalue()
            error = stderr.getvalue()
            
            print(f"Python stdout: {output}") # Debug print
            print(f"Python stderr: {error}") # Debug print
            
            if error:
                self._show_error(error)
            else:
                self.output_text.insert(tk.END, output)
        finally:
            # Restore stdout and stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def _run_c_cpp(self, code, language):
        """Run C/C++ code."""
        import tempfile
        import subprocess
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=f".{language}", delete=False) as f:
            f.write(code.encode())
            temp_file = f.name
        
        try:
            # Compile the code
            if language == "cpp":
                compile_cmd = ["g++", temp_file, "-o", f"{temp_file}.out"]
            else:
                compile_cmd = ["gcc", temp_file, "-o", f"{temp_file}.out"]
            
            compile_process = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True
            )
            
            if compile_process.returncode != 0:
                self._show_error(f"Compilation error:\n{compile_process.stderr}")
                return
            
            # Run the compiled program
            run_process = subprocess.run(
                [f"{temp_file}.out"],
                capture_output=True,
                text=True
            )
            
            if run_process.returncode != 0:
                self._show_error(f"Runtime error:\n{run_process.stderr}")
            else:
                self.output_text.insert(tk.END, run_process.stdout)
        finally:
            # Clean up temporary files
            import os
            os.unlink(temp_file)
            if os.path.exists(f"{temp_file}.out"):
                os.unlink(f"{temp_file}.out")

    def _run_java(self, code):
        """Run Java code."""
        import tempfile
        import subprocess
        
        # Extract class name from code
        class_match = re.search(r"public\s+class\s+(\w+)", code)
        if not class_match:
            self._show_error("No public class found in the code")
            return
        
        class_name = class_match.group(1)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".java", delete=False) as f:
            f.write(code.encode())
            temp_file = f.name
        
        try:
            # Compile the code
            compile_process = subprocess.run(
                ["javac", temp_file],
                capture_output=True,
                text=True
            )
            
            if compile_process.returncode != 0:
                self._show_error(f"Compilation error:\n{compile_process.stderr}")
                return
            
            # Run the compiled program
            run_process = subprocess.run(
                ["java", "-cp", os.path.dirname(temp_file), class_name],
                capture_output=True,
                text=True
            )
            
            if run_process.returncode != 0:
                self._show_error(f"Runtime error:\n{run_process.stderr}")
            else:
                self.output_text.insert(tk.END, run_process.stdout)
        finally:
            # Clean up temporary files
            import os
            os.unlink(temp_file)
            class_file = f"{temp_file[:-5]}.class"
            if os.path.exists(class_file):
                os.unlink(class_file)

    def _show_error(self, message):
        """Show error message in the output panel."""
        self.output_text.insert(tk.END, f"Error: {message}\n", "error")
        self.output_text.tag_configure("error", foreground="red")

    def _update_status(self, message):
        """Update the status bar message."""
        self.status_bar.config(text=message)

    def _import_lexer_rules(self):
        """Handle importing lexer rules from a JSON file."""
        from tkinter import filedialog
        
        filepath = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Select Lexer Rules File"
        )
        
        if filepath:
            self.lexer.load_rules_from_json(filepath)
            # After loading new rules, re-tokenize the current editor content
            # and update the DFA and token table
            self.on_editor_change() # This method already handles tokenizing and updating

def main():
    root = tk.Tk()
    app = LexViApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 