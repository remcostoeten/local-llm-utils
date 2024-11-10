#!/usr/bin/env python3

import os
import json
import requests
from typing import Optional, Dict, Tuple, List
import re
from pathlib import Path
import threading
import time
import sys
from dataclasses import dataclass
import functools

# ANSI Colors
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

class ProgressSpinner:
    """Animated progress spinner for long operations."""
    def __init__(self, message: str):
        self.message = message
        self.spinning = True
        self.spinner = threading.Thread(target=self._spin)
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.delay = 0.1

    def _spin(self):
        i = 0
        while self.spinning:
            frame = self.frames[i % len(self.frames)]
            sys.stdout.write(f"\r{CYAN}{frame} {self.message}...{RESET}")
            sys.stdout.flush()
            time.sleep(self.delay)
            i += 1

    def start(self):
        self.spinner.start()

    def stop(self, success: bool = True):
        self.spinning = False
        self.spinner.join()
        symbol = f"{GREEN}✓" if success else f"{RED}✗"
        sys.stdout.write(f"\r{symbol} {self.message}{RESET}\n")
        sys.stdout.flush()

class ComponentAnalyzer:
    """Analyzes TypeScript/React components."""
    
    def __init__(self):
        self.patterns = {
            'component_name': r'(?:export\s+)?(?:function|const|class)\s+(\w+)',
            'props_interface': r'interface\s+(\w+Props)\s*{([^}]+)}',
            'props_type': r'type\s+(\w+Props)\s*=\s*{([^}]+)}',
            'exports': r'export\s+(?:{([^}]+)}|default\s+(\w+))',
            'imports': r'import\s+[^;]+from\s+[\'"]([^\'"]+)[\'"]'
        }

    @functools.lru_cache(maxsize=32)
    def analyze(self, content: str) -> Dict[str, any]:
        """Analyze component structure and features."""
        info = {
            'name': '',
            'type': 'functional',
            'props': [],
            'exports': [],
            'imports': []
        }

        # Component name and type
        name_match = re.search(self.patterns['component_name'], content)
        if name_match:
            info['name'] = name_match.group(1)
            if 'React.Component' in content or 'Component' in content:
                info['type'] = 'class'

        # Props
        props_match = re.findall(r'(?:interface|type)\s+\w+Props\s*[={]([^}]+)}', content)
        if props_match:
            for props_content in props_match:
                props = re.findall(r'(\w+)(?:\??):\s*([^;\n]+)', props_content)
                info['props'].extend([{'name': p[0], 'type': p[1].strip()} for p in props])

        # Exports
        exports = re.findall(r'export\s+(?:const|function|class)\s+(\w+)', content)
        info['exports'] = exports

        return info

class FastLLMDocGenerator:
    """Fast documentation generator using local LLM."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "codellama"
        self.timeout = 5
        self.cache = {}
        self.analyzer = ComponentAnalyzer()

    def _call_llm_with_timeout(self, prompt: str, file_path: str, temperature: float = 0.3) -> str:
        """Make an LLM request with timeout and fallback."""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature,
                    "max_tokens": 200
                },
                timeout=self.timeout
            )
            return response.json()["response"].strip()
        except Exception as e:
            component_name = os.path.basename(file_path).replace('.tsx', '').replace('.ts', '')
            return f"A React component for {component_name} functionality."

    def generate_docs(self, file_path: str, detail_level: str = 'normal') -> Tuple[str, str]:
        """Generate component documentation and example."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            info = self.analyzer.analyze(content)
            example = self._generate_example(info)

            cache_key = f"{file_path}:{detail_level}"
            if cache_key in self.cache:
                description = self.cache[cache_key]
            else:
                prompt = self._create_description_prompt(info, detail_level)
                description = self._call_llm_with_timeout(prompt, file_path)
                self.cache[cache_key] = description

            return description, example

        except Exception as e:
            print(f"{RED}Error generating docs: {str(e)}{RESET}")
            component_name = os.path.basename(file_path).replace('.tsx', '').replace('.ts', '')
            return f"A React component for {component_name}.", self._generate_basic_example(component_name)

    def _create_description_prompt(self, info: Dict, detail_level: str) -> str:
        """Create an optimized prompt for description generation."""
        return f"""Write a {detail_level} description for React {info['type']} component {info['name']}.
Props: {', '.join(p['name'] for p in info['props'])}
Exports: {', '.join(info['exports'])}
Keep it concise and technical."""

    def _generate_example(self, info: Dict) -> str:
        """Generate a component usage example."""
        name = info['name']
        props = info['props']
        exports = info['exports'] or [name]

        example = [
            f"import {{ {', '.join(exports)} }} from './{name}'",
            "",
            "// Basic usage",
            f"export const Example = () => (",
            f"  <{name}"
        ]

        # Add example props if available
        for prop in props[:2]:
            if 'string' in prop['type'].lower():
                example.append(f'    {prop["name"]}="example"')
            elif 'number' in prop['type'].lower():
                example.append(f'    {prop["name"]}={1}')
            elif 'boolean' in prop['type'].lower():
                example.append(f'    {prop["name"]}={true}')
            elif 'function' in prop['type'].lower() or '=>' in prop['type']:
                example.append(f'    {prop["name"]}={{() => {{}}}}')

        example.extend([
            "  >",
            "    Example content",
            f"  </{name}>",
            ")"
        ])

        return '\n'.join(example)

    def _generate_basic_example(self, component_name: str) -> str:
        """Generate a minimal example when analysis fails."""
        return f"""import {{ {component_name} }} from './{component_name}'

// Basic usage
export const Example = () => (
  <{component_name}>
    Example content
  </{component_name}>
)"""

class DocWriter:
    """Handles writing documentation to files."""

    @staticmethod
    def write_docs(file_path: str, description: str, example: str) -> bool:
        """Write documentation to the component file."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Remove existing docstrings
            content = re.sub(r'/\*\*[\s\S]*?\*/', '', content)

            # Create new docstring
            doc_block = [
                "/**",
                " * @author Remco Stoeten",
                " *",
                f" * @description {description}",
                " *",
                " */",
                "",
                content.lstrip(),
                "",
                "/**",
                " * @example",
                " * " + "\n * ".join(example.split('\n')),
                " */",
                ""
            ]

            with open(file_path, 'w') as f:
                f.write('\n'.join(doc_block))

            return True

        except Exception as e:
            print(f"{RED}Error writing docs: {str(e)}{RESET}")
            return False

def find_components(search_dir: str, pattern: str) -> List[str]:
    """Find all matching component files."""
    matches = []
    for root, _, files in os.walk(search_dir):
        for file in files:
            if file.endswith(('.ts', '.tsx')) and pattern.lower() in file.lower():
                matches.append(os.path.join(root, file))
    return matches

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fast Documentation Generator")
    parser.add_argument('--find', help="Component pattern to search for")
    parser.add_argument('--generate-docs', action='store_true')

    args = parser.parse_args()

    if args.find and args.generate_docs:
        # Initialize generators
        generator = FastLLMDocGenerator()
        doc_writer = DocWriter()

        # Find UI directory
        ui_dir = os.path.join(os.path.dirname(os.getcwd()), 'ui')
        if not os.path.exists(ui_dir):
            ui_dir = os.getcwd()

        # Find matching components
        matches = find_components(ui_dir, args.find)

        if not matches:
            print(f"{RED}No components found{RESET}")
            return

        # Show matches
        print(f"\n{CYAN}Found components:{RESET}")
        for i, path in enumerate(matches, 1):
            print(f"{i}. {os.path.relpath(path, ui_dir)}")

        # Get selection
        choice = input(f"\n{YELLOW}Select components (comma-separated numbers or 'all'):{RESET} ")
        if not choice:
            return

        # Process selection
        selected = range(len(matches)) if choice.lower() == 'all' else \
                  [int(x.strip()) - 1 for x in choice.split(',')]

        # Process components
        total = len(selected)
        for idx, file_idx in enumerate(selected, 1):
            if 0 <= file_idx < len(matches):
                file_path = matches[file_idx]
                print(f"\n{CYAN}Processing ({idx}/{total}): {os.path.basename(file_path)}{RESET}")

                # Show spinner while generating
                spinner = ProgressSpinner("Generating documentation")
                spinner.start()

                # Generate and write docs
                description, example = generator.generate_docs(file_path)
                success = doc_writer.write_docs(file_path, description, example)

                spinner.stop(success)

if __name__ == "__main__":
    main()