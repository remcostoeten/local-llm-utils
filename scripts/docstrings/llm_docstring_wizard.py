
#!/usr/bin/env python3

import os
import json
import requests
from typing import Optional, Dict, Tuple, List, Any
import re
from pathlib import Path
import threading
import time
import sys
from dataclasses import dataclass
import functools
import ast
from enum import Enum
import asyncio
import concurrent.futures
import argparse

# ANSI Colors
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

class ComponentType(Enum):
    FUNCTIONAL = "functional"
    CLASS = "class"
    HOOK = "hook"
    HOC = "hoc"

@dataclass
class PropInfo:
    name: str
    type: str
    required: bool
    default_value: Optional[str]
    description: str = ""

@dataclass
class ComponentInfo:
    name: str
    type: ComponentType
    props: List[PropInfo]
    exports: List[str]
    imports: List[Dict[str, str]]
    hooks: List[str]
    dependencies: List[str]
    styles: Dict[str, Any]
    event_handlers: List[str]
    jsx_elements: List[str]

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
    """Advanced TypeScript/React component analyzer."""
    
    def __init__(self):
        self.patterns = {
            'component_name': r'(?:export\s+)?(?:function|const|class)\s+(\w+)',
            'props_interface': r'interface\s+(\w+Props)\s*{([^}]+)}',
            'props_type': r'type\s+(\w+Props)\s*=\s*{([^}]+)}',
            'exports': r'export\s+(?:{([^}]+)}|default\s+(\w+))',
            'imports': r'import\s+{([^}]+)}\s+from\s+[\'"]([^\'"]+)[\'"]',
            'hooks': r'use\w+(?:\s*\([^)]*\))?',
            'jsx_elements': r'<(\w+)[^>]*>',
            'event_handlers': r'on\w+\s*=\s*{([^}]+)}',
            'styles': r'(?:className|style)\s*=\s*(?:{[^}]+}|"[^"]+")',
            'default_props': r'static\s+defaultProps\s*=\s*({[^}]+})',
            'prop_types': r'static\s+propTypes\s*=\s*({[^}]+})',
        }

    def _extract_prop_info(self, prop_content: str) -> List[PropInfo]:
        """Extract detailed prop information including types, defaults, and requirements."""
        props = []
        prop_matches = re.finditer(r'(\w+)(\??):\s*([^;\n]+)(?:\s*=\s*([^;\n]+))?', prop_content)
        
        for match in prop_matches:
            name = match.group(1)
            required = match.group(2) != "?"
            prop_type = match.group(3).strip()
            default_value = match.group(4).strip() if match.group(4) else None
            
            props.append(PropInfo(
                name=name,
                type=prop_type,
                required=required,
                default_value=default_value
            ))
        
        return props

    def _detect_component_type(self, content: str) -> ComponentType:
        """Detect the type of React component."""
        if "React.Component" in content or "Component" in content:
            return ComponentType.CLASS
        elif "use" in content and "return" in content:
            return ComponentType.HOOK
        elif "withRouter" in content or "compose(" in content:
            return ComponentType.HOC
        return ComponentType.FUNCTIONAL

    @functools.lru_cache(maxsize=32)
    def analyze(self, content: str) -> ComponentInfo:
        """Perform comprehensive component analysis."""
        # Component name and type
        name_match = re.search(self.patterns['component_name'], content)
        name = name_match.group(1) if name_match else ""
        
        # Determine component type
        component_type = self._detect_component_type(content)
        
        # Extract props
        props = []
        props_matches = re.findall(r'(?:interface|type)\s+\w+Props\s*[={]([^}]+)}', content)
        for props_content in props_matches:
            props.extend(self._extract_prop_info(props_content))
        
        # Extract imports
        imports = []
        import_matches = re.finditer(self.patterns['imports'], content)
        for match in import_matches:
            items = [item.strip() for item in match.group(1).split(',')]
            source = match.group(2)
            imports.extend([{"item": item, "source": source} for item in items])
        
        # Extract hooks
        hooks = re.findall(self.patterns['hooks'], content)
        
        # Extract JSX elements
        jsx_elements = list(set(re.findall(self.patterns['jsx_elements'], content)))
        
        # Extract event handlers
        event_handlers = re.findall(self.patterns['event_handlers'], content)
        
        # Extract styles
        styles = {}
        style_matches = re.finditer(self.patterns['styles'], content)
        for match in style_matches:
            style_content = match.group(0)
            if 'className' in style_content:
                styles['classes'] = re.findall(r'"([^"]+)"', style_content)
            elif 'style' in style_content:
                styles['inline'] = re.findall(r'{([^}]+)}', style_content)
        
        # Extract exports
        exports = []
        export_matches = re.findall(r'export\s+(?:const|function|class)\s+(\w+)', content)
        exports.extend(export_matches)
        
        return ComponentInfo(
            name=name,
            type=component_type,
            props=props,
            exports=exports,
            imports=imports,
            hooks=hooks,
            dependencies=[imp["source"] for imp in imports],
            styles=styles,
            event_handlers=event_handlers,
            jsx_elements=jsx_elements
        )

class FastLLMDocGenerator:
    """Enhanced documentation generator using local LLM."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "codellama"
        self.timeout = 10
        self.cache = {}
        self.analyzer = ComponentAnalyzer()

    async def _call_llm_async(self, prompt: str, temperature: float = 0.3) -> str:
        """Make an async LLM request."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": temperature,
                        "max_tokens": 500
                    },
                    timeout=self.timeout
                ) as response:
                    result = await response.json()
                    return result["response"].strip()
            except Exception as e:
                return ""

    def _generate_smart_example(self, info: ComponentInfo) -> str:
        """Generate an intelligent, context-aware component usage example."""
        imports = []
        used_imports = set()
        
        # Add component import
        imports.append(f"import {{ {info.name} }} from './{info.name}'")
        
        # Add necessary imports from dependencies
        for imp in info.imports:
            if any(hook in imp["item"] for hook in info.hooks):
                imports.append(f"import {{ {imp['item']} }} from '{imp['source']}'")
                used_imports.add(imp["item"])
        
        example = [
            "// Advanced usage example",
            "export const Example = () => {",
        ]
        
        # Add hooks usage
        for hook in info.hooks:
            if hook.startswith("useState"):
                example.append(f"  const [state, setState] = useState(null)")
            elif hook.startswith("useEffect"):
                example.append(f"  useEffect(() => {{")
                example.append(f"    // Side effect logic")
                example.append(f"  }}, [])")
        
        # Generate props with smart defaults
        props = []
        for prop in info.props:
            if prop.default_value:
                props.append(f'    {prop.name}={prop.default_value}')
            else:
                if "string" in prop.type.lower():
                    props.append(f'    {prop.name}="example"')
                elif "number" in prop.type.lower():
                    props.append(f'    {prop.name}={42}')
                elif "boolean" in prop.type.lower():
                    props.append(f'    {prop.name}={true}')
                elif "function" in prop.type.lower() or "=>" in prop.type:
                    handler_name = f"handle{prop.name.capitalize()}"
                    example.insert(2, f"  const {handler_name} = () => {{")
                    example.insert(3, f"    console.log('{handler_name} called')")
                    example.insert(4, f"  }}")
                    example.insert(5, "")
                    props.append(f'    {prop.name}={{{handler_name}}}')
                elif "array" in prop.type.lower():
                    props.append(f'    {prop.name}={[1, 2, 3]}')
                elif "object" in prop.type.lower():
                    props.append(f'    {prop.name}={{{{ key: "value" }}}}')
        
        # Add component usage with props
        example.append("")
        example.append("  return (")
        example.append(f"    <{info.name}")
        example.extend(props)
        
        # Add children if component accepts them
        if any("children" in prop.name.lower() for prop in info.props):
            example.append("    >")
            example.append("      <div>Example Content</div>")
            example.append(f"    </{info.name}>")
        else:
            example.append("    />")
        
        example.extend([
            "  )",
            "}"
        ])
        
        # Combine imports and example
        return "\n".join(imports + ["", ""] + example)

    async def generate_docs(self, file_path: str, detail_level: str = 'normal') -> Tuple[str, str]:
        """Generate comprehensive component documentation and example."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            info = self.analyzer.analyze(content)
            example = self._generate_smart_example(info)

            cache_key = f"{file_path}:{detail_level}"
            if cache_key in self.cache:
                description = self.cache[cache_key]
            else:
                prompt = self._create_enhanced_prompt(info, detail_level)
                description = await self._call_llm_async(prompt)
                self.cache[cache_key] = description

            return description, example

        except Exception as e:
            print(f"{RED}Error generating docs: {str(e)}{RESET}")
            return f"Documentation generation failed.", self._generate_basic_example(info.name)

    def _create_enhanced_prompt(self, info: ComponentInfo, detail_level: str) -> str:
        """Create a detailed prompt for documentation generation."""
        component_details = {
            "name": info.name,
            "type": info.type.value,
            "props": [{"name": p.name, "type": p.type, "required": p.required} for p in info.props],
            "hooks": info.hooks,
            "dependencies": info.dependencies,
            "exports": info.exports
        }
        
        return f"""Create a {detail_level} technical documentation for a React component with these details:
{json.dumps(component_details, indent=2)}

Include:
1. Brief description
2. Key features
3. Props documentation
4. Usage considerations
5. Performance implications
6. Browser compatibility notes

Keep it concise and technical."""

class DocWriter:
    """Enhanced documentation writer with advanced formatting."""

    @staticmethod
    def write_docs(file_path: str, description: str, example: str) -> bool:
        """Write comprehensive documentation to the component file."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Remove existing docstrings
            content = re.sub(r'/\*\*[\s\S]*?\*/', '', content)

            # Create new docstring with enhanced structure
            doc_block = [
                "/**",
                " * @fileoverview",
                f" * {description}",
                " *",
                " * @author Automatically generated by DocumentationGenerator",
                " * @version 1.0.0",
                " * @module components",
                " * @since " + time.strftime("%Y-%m-%d"),
                " *",
                " * @example",
                " * ```tsx",
                " * " + "\n * ".join(example.split('\n')),
                " * ```",
                " */",
                "",
                content.lstrip()
            ]

            with open(file_path, 'w') as f:
                f.write('\n'.join(doc_block))

            return True

        except Exception as e:
            print(f"{RED}Error writing docs: {str(e)}{RESET}")
            return False

async def process_components(components: List[str], generator: FastLLMDocGenerator, doc_writer: DocWriter):
    """Process multiple components concurrently."""
    async def process_component(file_path: str):
        spinner = ProgressSpinner(f"Processing {os.path.basename(file_path)}")
        spinner.start()
        
        description, example = await generator.generate_docs(file_path)
        success = doc_writer.write_docs(file_path, description, example)
        
        spinner.stop(success)
        return file_path, success

    tasks = [process_component(component) for component in components]
    results = await asyncio.gather(*tasks)
    return results

def find_components(search_term: str, root_dir: str = ".", search_in_src: bool = False) -> list[str]:
    matches = []
    excluded_dirs = {'node_modules', '.git', '__pycache__', 'dist', 'build'}
    valid_extensions = {'.ts', '.tsx', '.js', '.jsx'}
    
    # Determine the starting directory
    start_dir = os.path.join(root_dir, 'src') if search_in_src else root_dir
    
    for root, dirs, files in os.walk(start_dir):
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        for file in files:
            if any(file.endswith(ext) for ext in valid_extensions):
                if search_term.lower() in file.lower():
                    full_path = os.path.join(root, file)
                    matches.append(full_path)
    
    return matches

async def main():
    import argparse
    import aiohttp

    parser = argparse.ArgumentParser(description="Advanced React Documentation Generator")
    parser.add_argument('--find', help="Component pattern to search for")
    parser.add_argument('--generate-docs', action='store_true')
    parser.add_argument('--detail-level', choices=['brief', 'normal', 'detailed'], default='normal',
                       help="Level of documentation detail")
    parser.add_argument('--exclude', help="Patterns to exclude (comma-separated)")
    parser.add_argument('--config', help="Path to configuration file")
    parser.add_argument('--output-format', choices=['jsdoc', 'tsdoc', 'markdown'], default='jsdoc',
                       help="Documentation format")
    parser.add_argument("--src-only", action="store_true", help="Search only in src directory")

    args = parser.parse_args()

    if args.config:
        try:
            with open(args.config) as f:
                config = json.load(f)
                # Override defaults with config file settings
                for key, value in config.items():
                    if not getattr(args, key, None):
                        setattr(args, key, value)
        except Exception as e:
            print(f"{RED}Error loading config: {str(e)}{RESET}")

    if args.find and args.generate_docs:
        # Initialize generators
        generator = FastLLMDocGenerator()
        doc_writer = DocWriter()

        # Find UI directory with smart detection
        possible_dirs = [
            os.path.join(os.path.dirname(os.getcwd()), 'ui'),
            os.path.join(os.getcwd(), 'src'),
            os.path.join(os.getcwd(), 'components'),
            os.getcwd()
        ]
        
        ui_dir = next((d for d in possible_dirs if os.path.exists(d)), os.getcwd())

        # Process exclude patterns
        exclude_patterns = [p.strip() for p in args.exclude.split(',')] if args.exclude else []

        def should_include_file(file_path: str) -> bool:
            """Check if file should be included based on exclude patterns."""
            return not any(pattern in file_path for pattern in exclude_patterns)

        # Find matching components with advanced filtering
        matches = []
        for root, _, files in os.walk(ui_dir):
            for file in files:
                if file.endswith(('.ts', '.tsx', '.jsx')) and args.find.lower() in file.lower():
                    full_path = os.path.join(root, file)
                    if should_include_file(full_path):
                        matches.append(full_path)

        if not matches:
            print(f"{RED}No components found matching '{args.find}'{RESET}")
            return

        # Show matches with additional info
        print(f"\n{CYAN}Found components:{RESET}")
        for i, path in enumerate(matches, 1):
            rel_path = os.path.relpath(path, ui_dir)
            size = os.path.getsize(path) / 1024  # Size in KB
            modified = time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(path)))
            print(f"{i}. {rel_path}")
            print(f"   Size: {size:.1f}KB | Modified: {modified}")

        # Get selection with validation
        while True:
            choice = input(f"\n{YELLOW}Select components (comma-separated numbers, ranges like 1-3, or 'all'):{RESET} ")
            if not choice:
                return

            try:
                if choice.lower() == 'all':
                    selected_indices = range(len(matches))
                    break
                
                selected_indices = set()
                for part in choice.split(','):
                    part = part.strip()
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        selected_indices.update(range(start - 1, end))
                    else:
                        selected_indices.add(int(part) - 1)
                
                if all(0 <= idx < len(matches) for idx in selected_indices):
                    selected_indices = sorted(selected_indices)
                    break
                else:
                    print(f"{RED}Invalid selection. Please use numbers between 1 and {len(matches)}{RESET}")
            except ValueError:
                print(f"{RED}Invalid input. Please use numbers, ranges, or 'all'{RESET}")

        # Process components with progress tracking
        total = len(selected_indices)
        print(f"\n{CYAN}Processing {total} component(s)...{RESET}")

        selected_components = [matches[idx] for idx in selected_indices]
        results = await process_components(selected_components, generator, doc_writer)

        # Show summary
        success_count = sum(1 for _, success in results if success)
        print(f"\n{GREEN}Documentation generation complete:{RESET}")
        print(f"- Successfully processed: {success_count}/{total} components")
        
        if success_count < total:
            print(f"{YELLOW}Failed components:{RESET}")
            for path, success in results:
                if not success:
                    print(f"- {os.path.relpath(path, ui_dir)}")

def run():
    """Entry point with error handling."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Process interrupted by user{RESET}")
    except Exception as e:
        print(f"\n{RED}Fatal error: {str(e)}{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    run()

