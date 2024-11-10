#!/usr/bin/env python3

import argparse
import os
import sys
import time
import shutil
import re
from typing import Optional, List
from datetime import datetime

class FuzzyFinder:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.excluded_dirs = {'node_modules', '.next', 'dist', 'build', '.git'}

    def find_ts_files(self) -> List[str]:
        """Find all TypeScript/TSX files in the project, excluding specified directories."""
        ts_files = []
        for root, dirs, files in os.walk(self.root_dir):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
            
            for file in files:
                if file.endswith(('.ts', '.tsx')):
                    rel_path = os.path.relpath(os.path.join(root, file), self.root_dir)
                    ts_files.append(rel_path)
        return sorted(ts_files)  # Sort files for better readability

    def fuzzy_match(self, query: str, files: List[str]) -> List[str]:
        """Simple fuzzy matching for file paths."""
        query_chars = list(query.lower())
        matches = []
        
        for file in files:
            file_lower = file.lower()
            pos = 0
            matched = True
            
            for char in query_chars:
                pos = file_lower.find(char, pos)
                if pos == -1:
                    matched = False
                    break
                pos += 1
            
            if matched:
                matches.append(file)
        
        return sorted(matches, key=lambda x: (
            # Sort by exact substring match first
            0 if query.lower() in x.lower() else 1,
            # Then by length of path
            len(x),
            # Then alphabetically
            x.lower()
        ))

    def interactive_search(self) -> str:
        """Interactive fuzzy file search."""
        files = self.find_ts_files()
        
        print(f"\n{CYAN}Found {len(files)} TypeScript files (excluding node_modules, .next){RESET}")
        print(f"\n{PURPLE}🔍 Fuzzy Search Mode{RESET}")
        print(f"{CYAN}Type any part of the file path - it doesn't need to be exact!{RESET}")
        print(f"{CYAN}Examples:{RESET}")
        print(f"{GREEN}• 'btn' will find 'button.tsx' and 'components/ui/button.tsx'{RESET}")
        print(f"{GREEN}• 'authform' will find 'auth-form.tsx' and 'features/auth/components/auth-form.tsx'{RESET}")
        
        while True:
            query = input(f"\n{CYAN}🔍 Search files (or press Enter to see all): {RESET}").strip()
            
            if not query:
                matches = files[:10]
                print(f"\n{PURPLE}Showing first 10 files. Type to search more specifically.{RESET}")
            else:
                matches = self.fuzzy_match(query, files)

            if not matches:
                print(f"{RED}No matches found. Try again.{RESET}")
                continue

            print(f"\n{CYAN}Matching files:{RESET}")
            for i, file in enumerate(matches[:10], 1):
                print(f"{GREEN}{i}.{RESET} {file}")

            if len(matches) > 10:
                print(f"\n{PURPLE}... and {len(matches) - 10} more matches. Please refine your search.{RESET}")

            choice = input(f"\n{CYAN}Select number or press Enter to search again: {RESET}").strip()
            
            if not choice:
                continue
                
            if choice.isdigit() and 1 <= int(choice) <= len(matches[:10]):
                selected_file = matches[int(choice) - 1]
                confirm = input(f"\n{CYAN}Use {GREEN}{selected_file}{CYAN}? [Y/n]: {RESET}").strip().lower()
                if confirm in ['', 'y', 'yes']:
                    return selected_file

            print(f"{RED}Invalid selection. Please try again.{RESET}")

def interactive_mode(utility: 'DocUtility') -> None:
    """Run the script in interactive mode."""
    print(f"{PURPLE}╔════════════════════════════════════════╗{RESET}")
    print(f"{PURPLE}║      {CYAN}DocString Wizard Interactive{PURPLE}      ║{RESET}")
    print(f"{PURPLE}╚════════════════════════════════════════╝{RESET}")

    # Fuzzy file finder
    finder = FuzzyFinder(utility.root_dir)
    file_path = finder.interactive_search()
    
    # Clear option
    clear_docs = input(f"\n{YELLOW}Clear existing docstrings? [y/N]: {RESET}").strip().lower() == 'y'
    
    if clear_docs:
        # Process file with clear option
        if utility.process_file(
            utility.resolve_path(file_path),
            None,  # description
            False,  # add_example
            True,  # clear_docs
            False,  # include_author
            None   # author_name
        ):
            utility.print_statistics(utility.resolve_path(file_path))
            print(f"\n{GREEN}Successfully cleared all docstrings! 🧹{RESET}\n")
        return

    # Author options
    include_author = input(f"\n{YELLOW}Include @author tag? [Y/n]: {RESET}").strip().lower() != 'n'
    
    if include_author:
        change_author = input(f"{YELLOW}Change author name from 'Remco Stoeten'? [y/N]: {RESET}").strip().lower() == 'y'
        author_name = input(f"{YELLOW}Enter author name: {RESET}").strip() if change_author else "Remco Stoeten"
    else:
        author_name = None

    # Description
    add_description = input(f"\n{YELLOW}Add description? [Y/n]: {RESET}").strip().lower() != 'n'
    description = input(f"{YELLOW}Enter description: {RESET}").strip() if add_description else None

    # Example block
    add_example = input(f"\n{YELLOW}Add example block? [y/N]: {RESET}").strip().lower() == 'y'

    # Process file
    resolved_path = utility.resolve_path(file_path)
    print(f"\n{CYAN}Processing file: {YELLOW}{resolved_path}{RESET}\n")

    if utility.process_file(
        resolved_path,
        description,
        add_example,
        False,  # clear_docs
        bool(author_name),
        author_name
    ):
        utility.print_statistics(resolved_path)
        print(f"\n{GREEN}Operation completed successfully! 🎉{RESET}\n")
    else:
        print(f"\n{RED}Operation failed! 😢{RESET}\n")
        sys.exit(1)

class DocUtility:
    def __init__(self):
        self.blocks_added = 0
        self.start_time = time.time()
        self.root_dir = self._find_project_root()

    def _find_project_root(self) -> str:
        """
        Finds the project root by looking for package.json
        """
        current = os.getcwd()
        while current != '/':
            if os.path.exists(os.path.join(current, 'package.json')):
                return current
            current = os.path.dirname(current)
        return os.getcwd()

    def resolve_path(self, file_path: str) -> str:
        """
        Resolves the file path relative to project root
        """
        if not os.path.isabs(file_path):
            return os.path.join(self.root_dir, file_path)
        return file_path

    def validate_file(self, file_path: str) -> bool:
        """
        Validates if the file exists and has the correct extension.
        """
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' does not exist.")
            return False
        
        if not file_path.endswith(('.ts', '.tsx')):
            print("Error: File must be a TypeScript (.ts) or TSX (.tsx) file.")
            return False
        
        return True

    def remove_docstrings(self, content: str) -> str:
        """
        Removes all JSDoc comments from the file
        """
        # Pattern to match JSDoc comments and any following empty lines
        pattern = r'/\*\*[\s\S]*?\*/\s*\n*'
        cleaned_content = re.sub(pattern, '', content)
        # Remove any remaining empty lines at the start of the file
        cleaned_content = re.sub(r'^\s*\n', '', cleaned_content)
        return cleaned_content

    def add_description(self, content: str, description: str, include_author: bool, author_name: str = "Remco Stoeten") -> str:
        """
        Adds a description block at the start of the file.
        """
        # First remove any existing docstrings
        content = self.remove_docstrings(content)
        
        doc_block = "/**\n"
        if include_author:
            doc_block += f" * @author {author_name}\n *\n"
        if description:
            doc_block += f" * @description {description}\n *\n"
        doc_block += " */\n\n"
        
        self.blocks_added += 1
        return doc_block + content

    def add_example(self, content: str) -> str:
        """
        Adds an example block at the end of the file.
        """
        # First remove any existing example blocks at the end
        content = re.sub(r'\s*/\*\*[\s\S]*?\*/\s*$', '', content)
        
        # Ensure there's exactly one newline before the example block
        content = content.rstrip() + "\n\n"
        doc_block = "/**\n * @example\n * \n */\n"
        self.blocks_added += 1
        return content + doc_block

    def process_file(self, file_path: str, description: Optional[str], add_example: bool, 
                    clear_docs: bool, include_author: bool, author_name: str = "Remco Stoeten") -> bool:
        """
        Processes the file and modifies documentation blocks.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if clear_docs:
                content = self.remove_docstrings(content)
                print(f"{GREEN}✓ Removed all documentation blocks{RESET}")
            else:
                if description or include_author:
                    content = self.add_description(content, description or "", include_author, author_name)
                    print(f"{GREEN}✓ Added description block at start of file{RESET}")
                
                if add_example:
                    content = self.add_example(content)
                    print(f"{GREEN}✓ Added example block at end of file{RESET}")

            # Create backup
            backup_path = f"{file_path}.bak"
            shutil.copy2(file_path, backup_path)

            # Write modified content
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            print(f"{RED}Error processing file: {str(e)}{RESET}")
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, file_path)
            return False

    def print_statistics(self, file_path: str) -> None:
        """
        Prints processing statistics.
        """
        processing_time = time.time() - self.start_time
        file_size = os.path.getsize(file_path) / 1024
        file_type = 'TSX' if file_path.endswith('.tsx') else 'TS'

        print("\nStatistics:")
        print(f"- Blocks added/modified: {self.blocks_added}")
        print(f"- File type: {file_type}")
        print(f"- File size: {file_size:.1f}KB")
        print(f"- Processing time: {processing_time:.2f}s")

def main():
    # ANSI color codes
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

    LOGO = f"""{PURPLE}
    ╔═══════════════════════════════════════════╗
    ║             {CYAN}DocString Wizard{PURPLE}              ║
    ║         {YELLOW}TypeScript Documentation CLI{PURPLE}         ║
    ╚═══════════════════════════════════════════╝{RESET}
    """

    description = f"""
{LOGO}{GREEN}
A magical tool for managing JSDoc documentation in TypeScript/TSX files.{RESET}

{BOLD}✨ Features:{RESET}
{CYAN}• 📝 Add/replace description blocks with optional @author tag
• 💡 Add/replace example blocks
• 🧹 Remove all documentation blocks
• 🎯 Handles paths relative to project root
• 💾 Creates backups before modifications{RESET}

{YELLOW}All paths are relative to the project root directory.{RESET}
"""

    epilog = f"""
{BOLD}🎮 Examples:{RESET}
{GREEN}
1. ✨ Add description with author:{RESET}
   {CYAN}python doc_utility.py -i src/components/button.tsx -d "Custom button component"{RESET}

{GREEN}2. 👤 Add description without author:{RESET}
   {CYAN}python doc_utility.py -i src/components/button.tsx -d "Custom button component" --no-author{RESET}

{GREEN}3. 💡 Add example block:{RESET}
   {CYAN}python doc_utility.py -i src/components/button.tsx -e{RESET}

{GREEN}4. 🎯 Add both description and example:{RESET}
   {CYAN}python doc_utility.py -i src/components/button.tsx -d "Custom button" -e{RESET}

{GREEN}5. 🧹 Remove all documentation:{RESET}
   {CYAN}python doc_utility.py -i src/components/button.tsx --clear{RESET}

{BOLD}📦 NPM Scripts:{RESET}
{YELLOW}You can also use npm scripts:{RESET}
• {CYAN}npm run docs -- -i src/components/button.tsx -d "Description"{RESET}
• {CYAN}npm run docs:clear -- -i src/components/button.tsx{RESET}

{BOLD}📝 Note:{RESET}
{RED}• Paths are relative to project root
• Existing documentation blocks will be replaced, not duplicated
• Original files are backed up before modification{RESET}
"""

    # Check if the terminal supports colors
    def supports_color():
        """Check if the terminal supports colors."""
        import sys
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

    # If terminal doesn't support colors, remove ANSI codes
    if not supports_color():
        for color in [PURPLE, CYAN, GREEN, YELLOW, RED, BOLD, RESET]:
            description = description.replace(color, '')
            epilog = epilog.replace(color, '')

    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '-i', '--input',
        required='--clear' not in sys.argv and '-c' not in sys.argv,
        help=f"{CYAN}Input file path (relative to project root){RESET}"
    )
    
    parser.add_argument(
        '-d', '--description',
        help=f"{GREEN}Add/replace description block with provided text{RESET}"
    )
    
    parser.add_argument(
        '-e', '--example',
        action='store_true',
        help=f"{YELLOW}Add/replace example block at the end of file{RESET}"
    )
    
    parser.add_argument(
        '-c', '--clear',
        action='store_true',
        help=f"{RED}Remove all documentation blocks from the file{RESET}"
    )
    
    parser.add_argument(
        '--no-author',
        action='store_true',
        help=f"{PURPLE}Skip adding @author Remco Stoeten tag in description block{RESET}"
    )

    # If no arguments provided, run interactive mode
    if len(sys.argv) == 1:
        utility = DocUtility()
        interactive_mode(utility)
        return

    args = parser.parse_args()
    utility = DocUtility()

    if args.clear:
        if not args.input:
            print(f"{RED}Error: --input is required with --clear{RESET}")
            sys.exit(1)

    resolved_path = utility.resolve_path(args.input)
    print(f"\n{CYAN}Processing file: {YELLOW}{resolved_path}{RESET}\n")
    
    if not utility.validate_file(resolved_path):
        sys.exit(1)
    
    if utility.process_file(
        resolved_path, 
        args.description, 
        args.example, 
        args.clear, 
        not args.no_author,
        "Remco Stoeten"
    ):
        utility.print_statistics(resolved_path)
        print(f"\n{GREEN}Operation completed successfully! 🎉{RESET}\n")
    else:
        print(f"\n{RED}Operation failed! 😢{RESET}\n")
        sys.exit(1)

if __name__ == "__main__":
    # Define ANSI color codes at the module level
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    main()
