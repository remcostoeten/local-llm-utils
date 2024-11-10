#!/usr/bin/env python3

import subprocess
import json
import os
from typing import Optional, Dict, List, Tuple
import requests
from pathlib import Path
import re

class DevLLMToolkit:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "codellama"  # Default model
        
    def switch_model(self, model_name: str) -> None:
        """Switch between different models based on task requirements."""
        self.model = model_name
        
    def _call_ollama(self, prompt: str, model: Optional[str] = None) -> str:
        """Make a request to the Ollama API with specific model."""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model or self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            print(f"Error calling Ollama: {str(e)}")
            return ""

    def analyze_code_quality(self, file_content: str) -> Dict[str, List[str]]:
        """Analyze code quality and suggest improvements."""
        prompt = f"""
Analyze this code and provide specific improvements for:
1. Performance
2. Security
3. Best practices
4. TypeScript-specific improvements

Code to analyze:
{file_content}

Format response as JSON with these categories as keys and lists of suggestions as values.
"""
        self.switch_model("codellama")  # Switch to code-specialized model
        response = self._call_ollama(prompt)
        try:
            return json.loads(response)
        except:
            return {"error": ["Failed to parse suggestions"]}

    def generate_unit_tests(self, file_content: str) -> str:
        """Generate unit tests for the given code."""
        prompt = f"""
Create Jest unit tests for this TypeScript code:

{file_content}

Include:
1. Common test cases
2. Edge cases
3. Mocking examples if needed
4. Only return the test code, no explanations
"""
        self.switch_model("codellama")
        return self._call_ollama(prompt)

    def explain_code_section(self, code_section: str) -> str:
        """Get a detailed explanation of a code section."""
        prompt = f"""
Explain this code section in detail:

{code_section}

Focus on:
1. What it does
2. Why it's implemented this way
3. Potential gotchas
4. Best practices used
"""
        self.switch_model("mistral")  # Switch to general-purpose model for explanations
        return self._call_ollama(prompt)

    def suggest_refactoring(self, file_content: str) -> Dict[str, str]:
        """Suggest code refactoring opportunities."""
        prompt = f"""
Analyze this code and suggest refactoring opportunities:

{file_content}

Consider:
1. Design patterns
2. Code organization
3. React best practices
4. TypeScript features

Return JSON with 'suggestions' and 'example' keys.
"""
        return json.loads(self._call_ollama(prompt))

    def generate_commit_message(self, diff: str) -> str:
        """Generate a semantic commit message from git diff."""
        prompt = f"""
Generate a semantic commit message for this diff:

{diff}

Follow format:
type(scope): description

Types: feat, fix, docs, style, refactor, test, chore
Keep it concise and descriptive.
"""
        self.switch_model("mistral")
        return self._call_ollama(prompt)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Development Tools with Local LLM")
    
    parser.add_argument('--analyze', help="Analyze code quality of a file")
    parser.add_argument('--test', help="Generate unit tests for a file")
    parser.add_argument('--explain', help="Explain a code section")
    parser.add_argument('--refactor', help="Suggest refactoring for a file")
    parser.add_argument('--commit', action='store_true', help="Generate commit message from staged changes")
    parser.add_argument('--model', help="Specify LLM model to use")
    
    args = parser.parse_args()
    toolkit = DevLLMToolkit()
    
    if args.model:
        toolkit.switch_model(args.model)
    
    if args.analyze:
        with open(args.analyze) as f:
            suggestions = toolkit.analyze_code_quality(f.read())
            print(json.dumps(suggestions, indent=2))
    
    elif args.test:
        with open(args.test) as f:
            tests = toolkit.generate_unit_tests(f.read())
            test_file = Path(args.test).with_suffix('.test.tsx')
            with open(test_file, 'w') as f:
                f.write(tests)
            print(f"Generated tests in {test_file}")
    
    elif args.explain:
        with open(args.explain) as f:
            explanation = toolkit.explain_code_section(f.read())
            print(explanation)
    
    elif args.refactor:
        with open(args.refactor) as f:
            suggestions = toolkit.suggest_refactoring(f.read())
            print(json.dumps(suggestions, indent=2))
    
    elif args.commit:
        diff = subprocess.getoutput('git diff --staged')
        if diff:
            message = toolkit.generate_commit_message(diff)
            print(f"\nSuggested commit message:\n{message}")

if __name__ == "__main__":
    main()