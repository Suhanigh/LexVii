# LexVi - Smart Learning Tool for Lexical Analysis and DFA

LexVi is an intelligent desktop application designed to help students learn Lexical Analysis and Deterministic Finite Automata (DFA) concepts through an interactive and educational interface.

## Features

- 🧠 Intelligent Code Editor with syntax highlighting and autocomplete
- 📊 Interactive DFA Visualizer with step-by-step animations
- 🌐 Multi-language support
- 🧪 Educational tools and practice quizzes
- 📝 Token Explorer with detailed explanations
- 💾 Save and load custom .lexvi files

## Requirements

- Python 3.8 or higher
- Tkinter (included with Python)

## Installation

1. Clone this repository:

```bash
git clone https://github.com/yourusername/lexvi.git
cd lexvi
```

2. Run the application:

```bash
python main.py
```

## Project Structure

- `main.py` - Application entry point
- `editor.py` - Code editor implementation
- `lexer.py` - Custom lexer logic
- `dfa_visualizer.py` - DFA visualization
- `localization.py` - Multi-language support
- `languages/` - Language pack directory
- `themes/` - UI theme definitions

## Adding New Languages

1. Create a new JSON file in the `languages/` directory (e.g., `hindi.json`)
2. Follow the format of existing language files
3. Add the language code to the language selector in the UI

## License

MIT License
