#!/usr/bin/env python3

import subprocess
import json
import os
from typing import Optional, Dict, List
import requests

class LLMDocStringEnhancer:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "codellama"  # CodeLlama is good for code-related tasks
    
    def _call_ollama(self, prompt: str) -> str:
        """Make a request to the Ollama API."""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            print(f"Error calling Ollama: {str(e)}")
            return ""

    def find_matching_file(self, query: str, project_root: str) -> Optional[str]:
        """Use LLM to find the most relevant TypeScript file based on description."""
        # Get list of TypeScript files
        ts_files = []
        for root, _, files in os.walk(project_root):
            if "node_modules" in root or ".next" in root:
                continue
            for file in files:
                if file.endswith(('.ts', '.tsx')):
                    rel_path = os.path.relpath(os.path.join(root, file), project_root)
                    ts_files.append(rel_path)

        prompt = f"""
Given these TypeScript files in a project:
{json.dumps(ts_files, indent=2)}

And this description of what I'm looking for:
"{query}"

Return only the most likely matching filename from the list above. Consider:
1. Semantic meaning (e.g., "button component" should match "Button.tsx")
2. File path structure (e.g., "auth form" might match "features/auth/AuthForm.tsx")
3. Return just the path, nothing else.
"""
        result = self._call_ollama(prompt).strip()
        return result if result in ts_files else None

    def generate_example(self, file_path: str, file_content: str) -> str:
        """Generate a relevant example for the TypeScript component/module."""
        prompt = f"""
Analyze this TypeScript file content and generate a JSDoc @example block showing how to use it:

{file_content}

Return only the example code that would go in the @example block. Include:
1. Import statement if needed
2. Basic usage example
3. Common props/options if it's a component
4. Keep it concise but practical
"""
        return self._call_ollama(prompt).strip()

def enhance_docstring_wizard():
    """Main function to enhance the DocString Wizard with LLM capabilities."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM-enhanced DocString Wizard")
    parser.add_argument(
        '--find',
        help="Natural language description of the file you're looking for"
    )
    parser.add_argument(
        '--generate-example',
        action='store_true',
        help="Automatically generate usage example"
    )
    parser.add_argument(
        '--description',
        help="Description to add to the docstring"
    )
    args, unknown = parser.parse_known_args()

    enhancer = LLMDocStringEnhancer()
    
    # Find project root
    project_root = os.getcwd()
    while project_root != '/' and not os.path.exists(os.path.join(project_root, 'package.json')):
        project_root = os.path.dirname(project_root)
    
    command = ['python3', 'doc_utility.py']  # Base command
    
    # If file finding is requested
    if args.find:
        matched_file = enhancer.find_matching_file(args.find, project_root)
        if matched_file:
            print(f"Found matching file: {matched_file}")
            command.extend(['-i', matched_file])
        else:
            print("No matching file found")
            return
    
    # Add description if provided
    if args.description:
        command.extend(['-d', args.description])
    
    # Generate and add example if requested
    if args.generate_example and args.find:
        with open(os.path.join(project_root, matched_file)) as f:
            content = f.read()
        example = enhancer.generate_example(matched_file, content)
        if example:
            command.append('-e')
            print("\nGenerated example will be added to the file.")
    
    # Execute the original script with enhanced arguments
    subprocess.run(command)

if __name__ == "__main__":
    enhance_docstring_wizard()
