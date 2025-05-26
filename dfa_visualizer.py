import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import math
from typing import Dict, List, Set, Tuple, Optional

class DFAState:
    def __init__(self, name: str, is_accepting: bool = False):
        self.name = name
        self.is_accepting = is_accepting
        self.transitions: Dict[str, 'DFAState'] = {}
        self.position: Tuple[int, int] = (0, 0)  # (x, y) coordinates

class DFAVisualizer(tk.Canvas):
    def __init__(self, master, theme=None, editor=None, **kwargs):
        self.theme = theme or {
            'dfa_bg': '#1e1e1e',
            'dfa_state': '#252526',
            'dfa_state_active': '#007acc',
            'dfa_state_accepting': '#2d2d2d',
            'foreground': '#d4d4d4',
        }
        super().__init__(master, bg=self.theme['dfa_bg'], highlightthickness=0, **kwargs)
        
        self.editor = editor # Store editor instance
        
        # DFA state
        self.states: Dict[str, DFAState] = {}
        self.current_state: Optional[DFAState] = None
        
        # Create default start state
        self.start_state = DFAState("START")
        self.states["START"] = self.start_state
        
        # Animation state
        self.animation_id = None
        self.animation_speed = 1000  # ms
        self.animation_step = 0
        self.animation_sequence: List[str] = []
        self.tokens: List['Token'] = [] # Store tokens here
        
        # Visual settings
        self.state_radius = 30
        self.arrow_length = 20
        self.state_spacing = 100
        
        # Customization state
        self.customization_mode = False
        self.selected_state = None
        self.dragging_state = None
        self.creating_transition = False
        self.transition_start = None
        
        # Bind events
        self.bind("<Configure>", self._on_configure)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Button-3>", self._on_right_click)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        
        # Create control buttons
        self._create_controls()
        
        # Create customization panel
        self._create_customization_panel()
        
        # Initial layout
        self._layout_states()
        self._draw_dfa()
    
    def _create_customization_panel(self):
        """Create the DFA customization panel."""
        self.custom_panel = ttk.Frame(self.master)
        self.custom_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        # Customization mode toggle
        self.custom_mode_var = tk.BooleanVar(value=False)
        self.custom_mode_btn = ttk.Checkbutton(
            self.custom_panel,
            text="Customization Mode",
            variable=self.custom_mode_var,
            command=self._toggle_customization_mode
        )
        self.custom_mode_btn.pack(pady=5)
        
        # State management
        state_frame = ttk.LabelFrame(self.custom_panel, text="State Management")
        state_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            state_frame,
            text="Add State",
            command=self._add_state
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            state_frame,
            text="Delete State",
            command=self._delete_state
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            state_frame,
            text="Toggle Accepting",
            command=self._toggle_accepting
        ).pack(fill=tk.X, pady=2)
        
        # Transition management
        trans_frame = ttk.LabelFrame(self.custom_panel, text="Transition Management")
        trans_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            trans_frame,
            text="Add Transition",
            command=self._start_transition
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            trans_frame,
            text="Delete Transition",
            command=self._delete_transition
        ).pack(fill=tk.X, pady=2)
    
    def _toggle_customization_mode(self):
        """Toggle DFA customization mode."""
        self.customization_mode = self.custom_mode_var.get()
        print(f"Customization mode toggled: {self.customization_mode}")
        if not self.customization_mode:
            self.selected_state = None
            self.creating_transition = False
            self.transition_start = None
            self._draw_dfa()
    
    def _add_state(self):
        """Add a new state to the DFA."""
        print("Add State button clicked")
        name = self._get_state_name()
        if name:
            state = DFAState(name)
            self.states[name] = state
            self._layout_states()
            self._draw_dfa()
            print(f"Added state: {name}")
    
    def _delete_state(self):
        """Delete the selected state."""
        print("Delete State button clicked")
        if self.selected_state and self.selected_state != self.start_state:
            # Remove transitions to/from this state
            for state in self.states.values():
                state.transitions = {k: v for k, v in state.transitions.items() if v != self.selected_state}
            del self.states[self.selected_state.name]
            self.selected_state = None
            self._layout_states()
            self._draw_dfa()
            print("Deleted selected state")
    
    def _toggle_accepting(self):
        """Toggle the accepting state of the selected state."""
        print("Toggle Accepting button clicked")
        if self.selected_state:
            self.selected_state.is_accepting = not self.selected_state.is_accepting
            self._draw_dfa()
            print(f"Toggled accepting for state: {self.selected_state.name}")
    
    def _start_transition(self):
        """Start creating a new transition."""
        print("Add Transition button clicked")
        if self.selected_state:
            self.creating_transition = True
            self.transition_start = self.selected_state
            print(f"Starting transition from state: {self.transition_start.name}")
    
    def _complete_transition(self, end_state: DFAState):
        """Complete the creation of a transition."""
        print(f"Attempting to complete transition to state: {end_state.name}")
        if self.creating_transition and self.transition_start and end_state:
            label = self._get_transition_label()
            if label:
                self.transition_start.transitions[label] = end_state
                self._draw_dfa()
                print(f"Added transition from {self.transition_start.name} to {end_state.name} with label {label}")
        self.creating_transition = False
        self.transition_start = None
        print("Transition creation process reset")
    
    def _delete_transition(self):
        """Delete a transition between states."""
        print("Delete Transition requested")
        # Delete transition from the selected state
        if self.selected_state:
            print(f"Selected state for deletion: {self.selected_state.name}")
            label = self._get_transition_label()
            if label and label in self.selected_state.transitions:
                print(f"Attempting to delete transition with label {label} from state {self.selected_state.name}")
                del self.selected_state.transitions[label]
                self._draw_dfa()
                print(f"Deleted transition with label {label} from state {self.selected_state.name}")
            elif label:
                print(f"Transition with label {label} not found in state {self.selected_state.name}")
            else:
                print("No transition label entered.")
        else:
            print("No state selected for transition deletion.")
    
    def _get_state_name(self) -> Optional[str]:
        """Get a new state name from the user."""
        print("Prompting for state name")
        name = tk.simpledialog.askstring("New State", "Enter state name:")
        print(f"Entered state name: {name}")
        if name and name not in self.states:
            return name
        return None
    
    def _get_transition_label(self) -> Optional[str]:
        """Get a transition label from the user."""
        print("Prompting for transition label")
        label = tk.simpledialog.askstring("Transition Label", "Enter transition label:")
        print(f"Entered transition label: {label}")
        return label
    
    def _on_click(self, event):
        """Handle mouse clicks on the canvas."""
        print(f"Canvas clicked at ({event.x}, {event.y})")
        if not self.customization_mode:
            print("Not in customization mode, ignoring click.")
            return
        
        # Find clicked state
        clicked_items = self.find_closest(event.x, event.y)
        print(f"Clicked items: {clicked_items}")
        if not clicked_items:
            print("No item clicked.")
            return
        
        tags = self.gettags(clicked_items[0])
        print(f"Tags of clicked item: {tags}")
        for tag in tags:
            print(f"Checking tag: {tag}")
            if tag in self.states:
                print(f"Clicked on state: {tag}")
                state = self.states[tag]
                if self.creating_transition:
                    print("Creating transition is true, completing transition.")
                    self._complete_transition(state)
                else:
                    print("Creating transition is false, selecting state.")
                    self.selected_state = state
                    self._draw_dfa()
                break
    
    def _on_right_click(self, event):
        """Handle right mouse clicks for context menu."""
        if not self.customization_mode:
            return
        
        # Find clicked state
        clicked_items = self.find_closest(event.x, event.y)
        if not clicked_items:
            return
        
        tags = self.gettags(clicked_items[0])
        for tag in tags:
            if tag in self.states:
                state = self.states[tag]
                self._show_state_context_menu(state, event.x_root, event.y_root)
                break
    
    def _on_drag(self, event):
        """Handle state dragging."""
        if not self.customization_mode or not self.selected_state:
            return
        
        # Update state position
        self.selected_state.position = (event.x, event.y)
        self._draw_dfa()
    
    def _on_release(self, event):
        """Handle mouse release."""
        if not self.customization_mode:
            return
        
        self.dragging_state = None
    
    def _show_state_context_menu(self, state: DFAState, x: int, y: int):
        """Show context menu for state operations."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Make Accepting", command=lambda: self._toggle_accepting())
        menu.add_command(label="Delete State", command=lambda: self._delete_state())
        menu.add_command(label="Add Transition", command=lambda: self._start_transition())
        menu.add_command(label="Delete Transition", command=lambda: self._delete_transition())
        menu.post(x, y)
    
    def _create_controls(self):
        """Create control buttons for the DFA visualizer."""
        control_frame = ttk.Frame(self.master)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.step_btn = ttk.Button(control_frame, text="Step", command=self.step_animation)
        self.step_btn.pack(side=tk.LEFT, padx=5)
        
        self.reset_btn = ttk.Button(control_frame, text="Reset", command=self.reset_animation)
        self.reset_btn.pack(side=tk.LEFT, padx=5)
        
        self.export_btn = ttk.Button(control_frame, text="Export", command=self.export_dfa)
        self.export_btn.pack(side=tk.LEFT, padx=5)
        
        self.minimize_btn = ttk.Button(control_frame, text="Minimize DFA", command=self._on_minimize_button_click)
        self.minimize_btn.pack(side=tk.LEFT, padx=5)
    
    def update_controls_text(self, step_text: str, reset_text: str, export_text: str):
        """Update the text of control buttons."""
        self.step_btn.config(text=step_text)
        self.reset_btn.config(text=reset_text)
        self.export_btn.config(text=export_text)
    
    def update_dfa(self, tokens: List['Token']):
        """Update the DFA based on the current tokens."""
        self.tokens = tokens # Store the updated tokens
        
        # Clear existing DFA
        self.states.clear()
        self.delete("all")
        
        # Create start state
        self.start_state = DFAState("START")
        self.states["START"] = self.start_state
        
        # Create states based on token types
        token_types = {token.type for token in tokens}
        
        # Create states for each token type
        for i, token_type in enumerate(token_types):
            state = DFAState(token_type, is_accepting=True)
            self.states[token_type] = state
            
            # Add transition from start state
            self.start_state.transitions[token_type] = state
        
        # Layout states in a circle
        self._layout_states()
        
        # Draw the DFA
        self._draw_dfa()
        
        # Reset animation
        self.reset_animation()
    
    def _layout_states(self):
        """Layout states in a circle."""
        if not self.states:
            return
            
        center_x = self.winfo_width() / 2
        center_y = self.winfo_height() / 2
        # Increase radius factor and add a minimum radius
        min_radius = 150 # Minimum radius to ensure some spacing
        radius = max(min_radius, min(center_x, center_y) * 0.8 - self.state_radius * 2)
        
        # Position start state
        self.start_state.position = (center_x - radius, center_y)
        
        # Position other states in a circle
        num_states = len(self.states) - 1  # Exclude start state
        if num_states > 0:
            for i, state in enumerate(self.states.values()):
                if state != self.start_state:
                    angle = 2 * math.pi * i / num_states
                    x = center_x + radius * math.cos(angle)
                    y = center_y + radius * math.sin(angle)
                    state.position = (x, y)
    
    def _draw_dfa(self):
        """Draw the DFA on the canvas."""
        # Draw transitions
        for state in self.states.values():
            for label, target in state.transitions.items():
                self._draw_transition(state, target, label)
        
        # Draw states
        for state in self.states.values():
            self._draw_state(state)
    
    def _draw_state(self, state: DFAState):
        """Draw a single state."""
        x, y = state.position
        
        fill_color = self.theme['dfa_state']
        if state == self.current_state:
            fill_color = self.theme['dfa_state_active']
        elif state.is_accepting:
            fill_color = self.theme['dfa_state_accepting']
        
        self.create_oval(
            x - self.state_radius,
            y - self.state_radius,
            x + self.state_radius,
            y + self.state_radius,
            fill=fill_color,
            outline="#007acc" if state == self.current_state else "#d4d4d4",
            width=2 if state == self.current_state else 1,
            tags=("state", state.name)
        )
        
        # Draw state name
        self.create_text(
            x, y,
            text="\n".join(state.name.split(", ")),
            fill=self.theme['foreground'],
            tags=("state_label", state.name),
            font=('Arial', max(8, 12 - len(max(state.name.split(", "), key=len)) // 2))
        )
        
        # Draw accepting state indicator
        if state.is_accepting:
            self.create_oval(
                x - self.state_radius + 5,
                y - self.state_radius + 5,
                x + self.state_radius - 5,
                y + self.state_radius - 5,
                outline="#d4d4d4",
                tags=("accepting", state.name)
            )
    
    def _draw_transition(self, from_state: DFAState, to_state: DFAState, label: str):
        """Draw a transition between states."""
        x1, y1 = from_state.position
        x2, y2 = to_state.position
        
        # Calculate arrow position
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        
        if length > 0:  # Avoid division by zero
            # Normalize direction vector
            dx /= length
            dy /= length
            
            # Calculate start and end points
            start_x = x1 + dx * self.state_radius
            start_y = y1 + dy * self.state_radius
            end_x = x2 - dx * self.state_radius
            end_y = y2 - dy * self.state_radius
            
            # Draw arrow line
            self.create_line(
                start_x, start_y,
                end_x, end_y,
                arrow=tk.LAST,
                fill="#d4d4d4",
                width=2,
                tags=("transition", f"{from_state.name}->{to_state.name}")
            )
            
            # Draw transition label
            label_x = (start_x + end_x) / 2
            label_y = (start_y + end_y) / 2
            
            # Add a small offset to the label position
            offset = 15 # Adjust this value for desired spacing
            perp_dx = -dy # Perpendicular vector
            perp_dy = dx
            
            # Normalize perpendicular vector
            perp_length = math.sqrt(perp_dx * perp_dx + perp_dy * perp_dy)
            if perp_length > 0:
                perp_dx /= perp_length
                perp_dy /= perp_length
                
                label_x += perp_dx * offset
                label_y += perp_dy * offset

            self.create_text(
                label_x, label_y,
                text=label,
                fill="#d4d4d4",
                tags=("transition_label", f"{from_state.name}->{to_state.name}")
            )
    
    def step_animation(self):
        """Step through the animation sequence and highlight token in editor."""
        if not self.animation_sequence or not self.tokens:
            return
        
        if self.animation_step >= len(self.animation_sequence):
            self.reset_animation()
            return
        
        # Clear previous highlighting
        if self.editor:
            self.editor.tag_remove('highlight', '1.0', tk.END)

        # Get current token value from the sequence
        token_value = self.animation_sequence[self.animation_step]
        
        # Find the corresponding token in the tokens list
        current_token = None
        if self.animation_step < len(self.tokens):
             current_token = self.tokens[self.animation_step]
        
        # Move to the next state based on the current state and token value
        if self.current_state is None:
            # Start from the initial state if not already started
            self.current_state = self.start_state
        
        if self.current_state and token_value in self.current_state.transitions:
            self.current_state = self.current_state.transitions[token_value]
        elif self.current_state is not None:
             # If no transition for the current token, the animation stops
             self.current_state = None # Indicate animation stopped due to no transition

        # Highlight current state in DFA
        self._highlight_state(self.current_state)
        
        # Highlight token in editor
        if self.editor and current_token:
             start = f"{current_token.line}.{current_token.column}"
             end = f"{current_token.line}.{current_token.column + len(current_token.value)}"
             self.editor.tag_add('highlight', start, end)
             self.editor.tag_config('highlight', background='yellow', foreground='black') # Or use theme colors
             self.editor.see(start) # Scroll to the highlighted token
        
        self.animation_step += 1
        
        # If animation finished, show result (accept or reject)
        if self.animation_step >= len(self.animation_sequence) or self.current_state is None:
             # Clear highlighting after animation finishes
             if self.editor:
                  self.editor.tag_remove('highlight', '1.0', tk.END)
                  
             if self.current_state and self.current_state.is_accepting:
                  print("Input accepted by DFA") # Or display in UI status bar
             else:
                  print("Input rejected by DFA") # Or display in UI status bar
    
    def reset_animation(self):
        """Reset the animation to the initial state."""
        self.animation_step = 0
        self.current_state = self.start_state # Reset to the start state
        self._clear_highlights()
        self._highlight_state(self.current_state) # Highlight the start state
        
        # Clear highlighting in editor
        if self.editor:
             self.editor.tag_remove('highlight', '1.0', tk.END)
    
    def _highlight_state(self, state: DFAState):
        """Highlight a state to show it's active."""
        self._clear_highlights()
        
        if state:
            # Find the state's circle
            state_items = self.find_withtag(state.name)
            for item in state_items:
                if "state" in self.gettags(item):
                    self.itemconfig(item, fill=self.theme['dfa_state_active'])
    
    def _clear_highlights(self):
        """Clear all state highlights."""
        for state in self.states.values():
            state_items = self.find_withtag(state.name)
            for item in state_items:
                if "state" in self.gettags(item):
                    fill_color = self.theme['dfa_state_accepting'] if state.is_accepting else self.theme['dfa_state']
                    self.itemconfig(item, fill=fill_color)
    
    def _on_configure(self, event):
        """Handle canvas resize."""
        self._layout_states()
        self.delete("all")
        self._draw_dfa()
    
    def _show_state_info(self, state: DFAState):
        """Show information about a state."""
        info = f"State: {state.name}\n"
        info += f"Type: {'Accepting' if state.is_accepting else 'Non-accepting'}\n"
        info += "Transitions:\n"
        for label, target in state.transitions.items():
            info += f"  {label} → {target.name}\n"
        
        # Create tooltip
        tooltip = tk.Toplevel(self)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{self.winfo_rootx() + 10}+{self.winfo_rooty() + 10}")
        
        label = ttk.Label(tooltip, text=info, justify=tk.LEFT,
                         background="#222", foreground="#d4d4d4", relief=tk.SOLID, borderwidth=1)
        label.pack()
        
        # Auto-destroy tooltip after 3 seconds
        self.after(3000, tooltip.destroy)
    
    def export_dfa(self):
        """Export the DFA diagram as a PNG file."""
        # TODO: Implement DFA export functionality
        from tkinter import filedialog
        
        # Ask user for save location
        filepath = filedialog.asksaveasfilename(
            defaultextension=".ps",
            filetypes=[("PostScript files", "*.ps"), ("All files", "*.*")],
            title="Export DFA as PostScript"
        )
        
        if filepath:
            try:
                # Export canvas to PostScript
                self.postscript(file=filepath, colormode='color')
                print(f"DFA exported successfully to {filepath}") # Or display in UI status bar
            except Exception as e:
                print(f"Error exporting DFA: {e}") # Or display in UI status bar
    
    def _on_minimize_button_click(self):
        """Handle the Minimize DFA button click."""
        print("Minimize DFA button clicked")
        minimized_states = self.minimize_dfa()
        
        # Update the visualizer to display the minimized DFA
        self.states = minimized_states
        # Find the new start state in the minimized states
        self.start_state = next((state for state in minimized_states.values() if state.name == "START"), None)
        if not self.start_state and minimized_states:
             # If no state is explicitly named START, pick the first one as a fallback (might not be correct)
             self.start_state = next(iter(minimized_states.values()))
             print("Warning: Could not find a state named START in minimized DFA. Using an arbitrary state as start.")

        self._layout_states()
        self.delete("all")
        self._draw_dfa()

    def minimize_dfa(self) -> Dict[str, DFAState]:
        """Minimize the current DFA using the partitioning algorithm."""
        # Get all input symbols
        alphabet = set()
        for state in self.states.values():
            alphabet.update(state.transitions.keys())
        
        # Initial partitioning: Accepting states (P1) and Non-accepting states (P0)
        accepting_states = {state for state in self.states.values() if state.is_accepting}
        non_accepting_states = {state for state in self.states.values() if not state.is_accepting}
        
        partitions = [non_accepting_states, accepting_states]
        new_partitions = []
        
        while new_partitions != partitions:
            if new_partitions:
                partitions = new_partitions
            new_partitions = []
            
            for partition in partitions:
                # If partition is empty, add it back
                if not partition:
                    new_partitions.append(partition)
                    continue
                    
                # Group states within the partition
                groups = {}
                for state in partition:
                    # Create a key based on transitions to other partitions
                    transition_key = []
                    for symbol in sorted(list(alphabet)): # Sort symbols for consistent key
                        next_state = state.transitions.get(symbol)
                        # Find which partition the next state belongs to
                        next_partition_index = -1
                        if next_state:
                            for i, p in enumerate(partitions):
                                if next_state in p:
                                    next_partition_index = i
                                    break
                        transition_key.append(next_partition_index)
                    
                    key = tuple(transition_key)
                    
                    if key not in groups:
                        groups[key] = []
                    groups[key].append(state)
                
                # Add groups as new partitions
                new_partitions.extend(groups.values())
        
        # Create minimized DFA states
        minimized_states: Dict[str, DFAState] = {}
        partition_to_state = {}
        state_counter = 0
        
        # Create a mapping from original states to minimized states
        original_to_minimized = {}
        for i, partition in enumerate(new_partitions):
             if not partition:
                  continue
             
             # Create a comma-separated name from the original states in the partition
             original_state_names = sorted([s.name for s in partition])
             new_state_name = ", ".join(original_state_names)

             # If the original start state is in this partition, ensure the new state is marked as the start state
             is_start_state = self.start_state in partition

             # Determine if the new state is accepting
             is_accepting_state = any(s.is_accepting for s in partition)

             minimized_state = DFAState(new_state_name, is_accepting_state)
             
             # Handle the start state explicitly if this partition contains the original start state
             if is_start_state:
                  # We'll set this minimized state as the visualizer's start state later
                  pass # Keep the generated name for now, will handle the start state reference after creating all minimized states.
                  
             minimized_states[new_state_name] = minimized_state
             partition_to_state[i] = minimized_state
             for original_state in partition:
                 original_to_minimized[original_state] = minimized_state

        # Define transitions for minimized states
        for i, partition in enumerate(new_partitions):
             if not partition:
                  continue
             
             minimized_state = partition_to_state[i]
             original_state_in_partition = next(iter(partition)) # Use any state in the partition to find transitions
             
             for symbol, next_original_state in original_state_in_partition.transitions.items():
                  # Find the minimized state corresponding to the next original state
                  next_minimized_state = original_to_minimized.get(next_original_state)
                  if next_minimized_state:
                      minimized_state.transitions[symbol] = next_minimized_state

        # Find the new start state
        new_start_state = None
        for partition in new_partitions:
            if self.start_state in partition:
                new_start_state = original_to_minimized[self.start_state]
                break
                
        # Update the start state reference in the minimized states dictionary
        if new_start_state and "START" in minimized_states:
             # If a state named START exists (from the original DFA), ensure it's the new start state
             # Otherwise, rename the identified new_start_state to START if necessary
             if minimized_states["START"] != new_start_state:
                  # This case might happen if the original START state was merged with others.
                  # We need to rename the new start state's key in the dictionary.
                  original_name = new_start_state.name
                  new_start_state.name = "START"
                  minimized_states["START"] = new_start_state
                  del minimized_states[original_name]
                  # Update the name in the original_to_minimized map as well if needed
                  for original_state, minimized in original_to_minimized.items():
                       if minimized == new_start_state and original_state != self.start_state:
                            # This part is tricky and might need more robust handling depending on how state names are used.
                            # For simplicity now, we assume renaming the minimized state is sufficient.
                            pass # Further logic might be needed here depending on naming requirements.
        elif new_start_state and "START" not in minimized_states:
             # If no state named START exists, rename the new_start_state to START and add it
             new_start_state.name = "START"
             minimized_states["START"] = new_start_state

        # Re-layout the minimized DFA
        # Note: Layout needs to be done on the visualizer instance that will display these states.
        # We won't do layout here, as this method just returns the minimized DFA structure.

        return minimized_states 