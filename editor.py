import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Tuple
import re
from lexer import Lexer

class CodeEditor(tk.Text):
    def __init__(self, master, theme=None, **kwargs):
        self.theme = theme or {
            'background': '#1e1e1e',
            'foreground': '#d4d4d4',
            'cursor': '#d4d4d4',
            'selection_bg': '#264f78',
            'selection_fg': '#d4d4d4',
            'line_number_bg': '#1e1e1e',
            'line_number_fg': '#858585',
            'syntax': {
                'keyword': '#569cd6',
                'string': '#ce9178',
                'comment': '#6a9955',
                'function': '#dcdcaa',
                'number': '#b5cea8',
                'operator': '#d4d4d4',
                'identifier': '#9cdcfe'
            }
        }
        
        super().__init__(master, **kwargs)
        
        # Configure editor
        self.configure(
            bg=self.theme['editor_bg'] if 'editor_bg' in self.theme else self.theme['background'],
            fg=self.theme['editor_fg'] if 'editor_fg' in self.theme else self.theme['foreground'],
            insertbackground=self.theme['editor_cursor'] if 'editor_cursor' in self.theme else self.theme['cursor'],
            selectbackground=self.theme['editor_selection'] if 'editor_selection' in self.theme else self.theme['selection_bg'],
            selectforeground=self.theme['selection_fg'] if 'selection_fg' in self.theme else self.theme['foreground'],
            font=('Consolas', 12),
            wrap=tk.NONE,
            undo=True
        )
        
        # Create line numbers
        self.line_numbers = tk.Text(
            self.master,
            width=4,
            padx=3,
            pady=5,
            takefocus=0,
            border=0,
            background=self.theme['gutter_bg'] if 'gutter_bg' in self.theme else self.theme['background'],
            foreground=self.theme['gutter_fg'] if 'gutter_fg' in self.theme else self.theme['foreground'],
            font=('Consolas', 12)
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Configure tags for syntax highlighting
        self._configure_tags()
        
        # Initialize lexer
        self.lexer = Lexer()
        self.current_language = "python"
        
        # Suggestion state
        self.suggestion_window = None
        self.suggestions = []
        self.current_suggestion = 0
        
        # Bind events
        self.bind('<KeyRelease>', self._on_key_release)
        self.bind('<Key>', self._on_key)
        self.bind('<Button-1>', self._on_click)
        self.bind('<MouseWheel>', self._on_mousewheel)
        
        # Initialize line numbers
        self._update_line_numbers()
    
    def _configure_tags(self):
        """Configure syntax highlighting tags."""
        # Define the token types we expect to highlight and their corresponding theme keys
        syntax_types = {
            'keyword': 'keyword',
            'string': 'string',
            'comment': 'comment',
            'function': 'function',
            'number': 'number',
            'operator': 'operator',
            'identifier': 'identifier'
        }
        
        # Remove existing tags
        for tag in syntax_types.keys():
            self.tag_remove(tag, '1.0', tk.END)
        
        # Configure tags based on theme
        for token_type, theme_key in syntax_types.items():
            color = self.theme.get(theme_key)
            if color:
                self.tag_configure(token_type, foreground=color)
        
        # Configure other tags (error, warning, info)
        error_color = self.theme.get('error', '#f44747')
        warning_color = self.theme.get('warning', '#cca700')
        info_color = self.theme.get('info', '#3794ff')
        
        self.tag_configure('error', foreground=error_color)
        self.tag_configure('warning', foreground=warning_color)
        self.tag_configure('info', foreground=info_color)
    
    def set_language(self, language: str):
        """Set the current programming language."""
        self.current_language = language
        self.lexer = Lexer(language)
        self._highlight_syntax()
    
    def _on_key_release(self, event):
        """Handle key release events."""
        print(f"Key released: {event.char}")
        print(f"Editor has focus: {self.focus_get() == self}")
        if event.char and event.char.isprintable():
            self._highlight_syntax()
            self._show_suggestions()
        self._update_line_numbers()
        self.event_generate('<<TextChanged>>')
    
    def _on_key(self, event):
        """Handle key press events."""
        print(f"Key pressed: {event.keysym}")
        if self.suggestion_window and event.keysym in ('Up', 'Down', 'Return', 'Escape'):
            if event.keysym == 'Up':
                self._select_previous_suggestion()
            elif event.keysym == 'Down':
                self._select_next_suggestion()
            elif event.keysym == 'Return':
                self._apply_suggestion()
            elif event.keysym == 'Escape':
                self._hide_suggestions()
            return 'break'
    
    def _on_click(self, event):
        """Handle mouse click events."""
        self._hide_suggestions()
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel events."""
        self.line_numbers.yview_moveto(self.yview()[0])
    
    def _update_line_numbers(self):
        """Update the line numbers display."""
        self.line_numbers.delete('1.0', tk.END)
        line_count = self.get('1.0', tk.END).count('\n')
        for i in range(1, line_count + 1):
            self.line_numbers.insert(tk.END, f'{i}\n')
    
    def _highlight_syntax(self):
        """Apply syntax highlighting to the current text."""
        # Define the token types we expect to highlight
        syntax_tags = [
            'keyword',
            'string',
            'comment',
            'function',
            'number',
            'operator',
            'identifier'
        ]
        
        # Remove existing tags
        for tag in syntax_tags:
            self.tag_remove(tag, '1.0', tk.END)
        
        # Get current text
        text = self.get('1.0', tk.END)
        
        # Tokenize and highlight
        tokens = self.lexer.tokenize(text)
        for token in tokens:
            if token.type in syntax_tags:
                start = f"{token.line}.{token.column}"
                end = f"{token.line}.{token.column + len(token.value)}"
                self.tag_add(token.type, start, end)
    
    def _show_suggestions(self):
        """Show code suggestions based on current context."""
        print("Showing suggestions...")
        # Get current word and cursor position
        cursor_pos = self.index(tk.INSERT)
        text = self.get('1.0', cursor_pos)
        
        # Get suggestions from lexer
        suggestions = self.lexer.get_suggestions(text, len(text))
        print(f"Suggestions found: {suggestions}")
        
        if suggestions:
            self.suggestions = suggestions
            self.current_suggestion = 0
            self._create_suggestion_window()
        else:
            self._hide_suggestions()
    
    def _create_suggestion_window(self):
        """Create and show the suggestion window."""
        print("Creating suggestion window...")
        if self.suggestion_window:
            self.suggestion_window.destroy()
        
        # Get cursor position
        cursor_pos = self.index(tk.INSERT)
        bbox = self.bbox(cursor_pos)
        if not bbox:
            return
        
        x, y = bbox[0], bbox[1] + bbox[3]
        
        # Create suggestion window
        self.suggestion_window = tk.Toplevel(self)
        self.suggestion_window.wm_overrideredirect(True)
        self.suggestion_window.wm_geometry(f"+{self.winfo_rootx() + x}+{self.winfo_rooty() + y}")
        
        # Create suggestion list
        self.suggestion_list = tk.Listbox(
            self.suggestion_window,
            bg=self.theme.get('editor_bg', self.theme.get('background')),
            fg=self.theme.get('editor_fg', self.theme.get('foreground')),
            selectbackground=self.theme.get('editor_selection', self.theme.get('selection_bg')),
            selectforeground=self.theme.get('editor_fg', self.theme.get('foreground')),
            font=self['font'],
            height=min(len(self.suggestions), 5)
        )
        self.suggestion_list.pack()
        
        # Add suggestions
        for suggestion in self.suggestions:
            self.suggestion_list.insert(tk.END, suggestion)
        
        # Select first suggestion
        self.suggestion_list.selection_set(0)
    
    def _hide_suggestions(self):
        """Hide the suggestion window."""
        if self.suggestion_window:
            self.suggestion_window.destroy()
            self.suggestion_window = None
    
    def _select_next_suggestion(self):
        """Select the next suggestion in the list."""
        if self.suggestion_list:
            current = self.suggestion_list.curselection()[0]
            next_idx = (current + 1) % len(self.suggestions)
            self.suggestion_list.selection_clear(current)
            self.suggestion_list.selection_set(next_idx)
            self.suggestion_list.see(next_idx)
    
    def _select_previous_suggestion(self):
        """Select the previous suggestion in the list."""
        if self.suggestion_list:
            current = self.suggestion_list.curselection()[0]
            prev_idx = (current - 1) % len(self.suggestions)
            self.suggestion_list.selection_clear(current)
            self.suggestion_list.selection_set(prev_idx)
            self.suggestion_list.see(prev_idx)
    
    def _apply_suggestion(self):
        """Apply the selected suggestion."""
        if self.suggestion_list:
            selected = self.suggestion_list.get(self.suggestion_list.curselection())
            
            # Get current word
            cursor_pos = self.index(tk.INSERT)
            line, col = map(int, cursor_pos.split('.'))
            line_text = self.get(f"{line}.0", f"{line}.{col}")
            
            # Find word start
            word_start = col
            while word_start > 0 and line_text[word_start - 1].isalnum():
                word_start -= 1
            
            # Replace word with suggestion
            self.delete(f"{line}.{word_start}", cursor_pos)
            self.insert(f"{line}.{word_start}", selected)
            
            self._hide_suggestions()
            self.event_generate('<<TextChanged>>')
    
    def zoom_in(self):
        """Increase font size."""
        current_size = int(self['font'].split()[-1])
        if current_size < 24:
            self.configure(font=("Consolas", current_size + 1))
            self.line_numbers.configure(font=("Consolas", current_size + 1))
    
    def zoom_out(self):
        """Decrease font size."""
        current_size = int(self['font'].split()[-1])
        if current_size > 8:
            self.configure(font=("Consolas", current_size - 1))
            self.line_numbers.configure(font=("Consolas", current_size - 1)) 