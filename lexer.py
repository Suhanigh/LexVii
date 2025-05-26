from typing import List, Dict, Set, Optional
import re
import json

class Token:
    def __init__(self, type: str, value: str, line: int, column: int):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

class Lexer:
    def __init__(self, language: str = "python"):
        self.language = language
        self.keywords = self._get_language_keywords()
        self.operators = self._get_language_operators()
        self.patterns = self._get_language_patterns()
        
    def load_rules_from_json(self, filepath: str):
        """Load lexer rules from a JSON file."""
        try:
            with open(filepath, 'r') as f:
                rules = json.load(f)
            
            if 'patterns' in rules and isinstance(rules['patterns'], dict):
                self.patterns = rules['patterns']
                print(f"Loaded {len(self.patterns)} patterns from {filepath}")
            else:
                print(f"Warning: 'patterns' key not found or is not a dictionary in {filepath}")
                
            if 'keywords' in rules and isinstance(rules['keywords'], list):
                self.keywords = set(rules['keywords'])
                print(f"Loaded {len(self.keywords)} keywords from {filepath}")
            else:
                print(f"Warning: 'keywords' key not found or is not a list in {filepath}")
                
            if 'operators' in rules and isinstance(rules['operators'], list):
                self.operators = set(rules['operators'])
                print(f"Loaded {len(self.operators)} operators from {filepath}")
            else:
                print(f"Warning: 'operators' key not found or is not a list in {filepath}")
                
        except FileNotFoundError:
            print(f"Error: Rules file not found at {filepath}")
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {filepath}")
        except Exception as e:
            print(f"An unexpected error occurred while loading rules: {e}")
    
    def _get_language_keywords(self) -> Set[str]:
        """Get keywords for the current language."""
        keywords = {
            "python": {
                "and", "as", "assert", "break", "class", "continue", "def", "del", "elif", "else",
                "except", "False", "finally", "for", "from", "global", "if", "import", "in", "is",
                "lambda", "None", "nonlocal", "not", "or", "pass", "raise", "return", "True", "try",
                "while", "with", "yield"
            },
            "cpp": {
                "auto", "break", "case", "char", "const", "continue", "default", "do", "double",
                "else", "enum", "extern", "float", "for", "goto", "if", "int", "long", "register",
                "return", "short", "signed", "sizeof", "static", "struct", "switch", "typedef",
                "union", "unsigned", "void", "volatile", "while", "class", "namespace", "new",
                "delete", "public", "private", "protected", "this", "true", "false", "nullptr"
            },
            "java": {
                "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char", "class",
                "const", "continue", "default", "do", "double", "else", "enum", "extends", "final",
                "finally", "float", "for", "if", "implements", "import", "instanceof", "int",
                "interface", "long", "native", "new", "package", "private", "protected", "public",
                "return", "short", "static", "strictfp", "super", "switch", "synchronized", "this",
                "throw", "throws", "transient", "try", "void", "volatile", "while", "true", "false",
                "null"
            }
        }
        return keywords.get(self.language, set())
    
    def _get_language_operators(self) -> Set[str]:
        """Get operators for the current language."""
        operators = {
            "python": {
                "+", "-", "*", "/", "//", "%", "**", "=", "+=", "-=", "*=", "/=", "//=", "%=",
                "**=", "==", "!=", "<", ">", "<=", ">=", "and", "or", "not", "is", "in", "&", "|",
                "^", "~", "<<", ">>", "&=", "|=", "^=", "<<=", ">>="
            },
            "cpp": {
                "+", "-", "*", "/", "%", "++", "--", "=", "+=", "-=", "*=", "/=", "%=", "==", "!=",
                "<", ">", "<=", ">=", "&&", "||", "!", "&", "|", "^", "~", "<<", ">>", "&=", "|=",
                "^=", "<<=", ">>=", "->", ".", "::", "?", ":"
            },
            "java": {
                "+", "-", "*", "/", "%", "++", "--", "=", "+=", "-=", "*=", "/=", "%=", "==", "!=",
                "<", ">", "<=", ">=", "&&", "||", "!", "&", "|", "^", "~", "<<", ">>", "&=", "|=",
                "^=", "<<=", ">>=", "->", ".", "?", ":"
            }
        }
        return operators.get(self.language, set())
    
    def _get_language_patterns(self) -> Dict[str, str]:
        """Get regex patterns for the current language."""
        patterns = {
            "python": {
                "identifier": r"[a-zA-Z_][a-zA-Z0-9_]*",
                "string": r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'',
                "number": r"\d+(?:\.\d+)?(?:[eE][+-]?\d+)?",
                "comment": r"#.*$",
                "whitespace": r"\s+"
            },
            "cpp": {
                "identifier": r"[a-zA-Z_][a-zA-Z0-9_]*",
                "string": r'"(?:[^"\\]|\\.)*"',
                "number": r"\d+(?:\.\d+)?(?:[eE][+-]?\d+)?",
                "comment": r"//.*$|/\*[\s\S]*?\*/",
                "whitespace": r"\s+"
            },
            "java": {
                "identifier": r"[a-zA-Z_][a-zA-Z0-9_]*",
                "string": r'"(?:[^"\\]|\\.)*"',
                "number": r"\d+(?:\.\d+)?(?:[eE][+-]?\d+)?",
                "comment": r"//.*$|/\*[\s\S]*?\*/",
                "whitespace": r"\s+"
            }
        }
        return patterns.get(self.language, {})
    
    def tokenize(self, text: str) -> List[Token]:
        """Tokenize the input text."""
        tokens = []
        line = 1
        column = 1
        pos = 0
        
        while pos < len(text):
            # Try to match each pattern
            matched = False
            for token_type, pattern in self.patterns.items():
                match = re.match(pattern, text[pos:])
                if match:
                    value = match.group(0)
                    if token_type != "whitespace" and token_type != "comment":
                        if token_type == "identifier":
                            if value in self.keywords:
                                token_type = "keyword"
                            elif value in self.operators:
                                token_type = "operator"
                        tokens.append(Token(token_type, value, line, column))
                    
                    # Update position and column
                    pos += len(value)
                    column += len(value)
                    if token_type == "whitespace" and "\n" in value:
                        line += value.count("\n")
                        column = 1 + value.rindex("\n")
                    matched = True
                    break
            
            if not matched:
                # Handle single-character tokens (operators, etc.)
                char = text[pos]
                if char in self.operators:
                    tokens.append(Token("operator", char, line, column))
                else:
                    tokens.append(Token("unknown", char, line, column))
                pos += 1
                column += 1
        
        return tokens
    
    def get_suggestions(self, text: str, cursor_pos: int) -> List[str]:
        """Get token suggestions based on the current context."""
        suggestions = []
        
        # Get the word being typed
        word_start = cursor_pos
        while word_start > 0 and text[word_start - 1].isalnum():
            word_start -= 1
        current_word = text[word_start:cursor_pos]
        
        # Add keyword suggestions
        for keyword in self.keywords:
            if keyword.startswith(current_word):
                suggestions.append(keyword)
        
        # Add operator suggestions
        for operator in self.operators:
            if operator.startswith(current_word):
                suggestions.append(operator)
        
        return sorted(suggestions) 