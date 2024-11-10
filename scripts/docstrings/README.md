# DocString Wizard

This directory contains scripts to enhance and manage JSDoc documentation in TypeScript/TSX files. The main scripts are `doc_utility.py` and `llm_docstring_wizard.py`.

## Scripts

### `doc_utility.py`

This script provides various utilities to manage JSDoc documentation in TypeScript/TSX files.

#### Features

- **Add/replace description blocks** with optional `@author` tag
- **Add/replace example blocks** at the end of the file
- **Remove all documentation blocks**
- **Interactive fuzzy file search** to easily find and select files

#### Usage

1. **Add description with author:**
    ```sh
    python doc_utility.py -i src/components/button.tsx -d "Custom button component"
    ```

2. **Add description without author:**
    ```sh
    python doc_utility.py -i src/components/button.tsx -d "Custom button component" --no-author
    ```

3. **Add example block:**
    ```sh
    python doc_utility.py -i src/components/button.tsx -e
    ```

4. **Add both description and example:**
    ```sh
    python doc_utility.py -i src/components/button.tsx -d "Custom button" -e
    ```

5. **Remove all documentation:**
    ```sh
    python doc_utility.py -i src/components/button.tsx --clear
    ```

### `llm_docstring_wizard.py`

This script enhances the `doc_utility.py` script with LLM (Large Language Model) capabilities to find and document files based on natural language descriptions.

#### Features

- **Find and document a file based on description**
- **Generate appropriate examples if requested**

#### Usage

1. **Find and document a file based on description:**
    ```sh
    python llm_docstring_wizard.py --find "button component" --description "Custom button component" --generate-example
    ```

2. **Just find a file:**
    ```sh
    python llm_docstring_wizard.py --find "auth form component"
    ```

3. **Find a file and add generated example:**
    ```sh
    python llm_docstring_wizard.py --find "modal component" --generate-example
    ```

#### How It Works

1. Uses the LLM to find the most relevant TypeScript file based on your description.
2. Generates appropriate examples if requested.
3. Calls `doc_utility.py` with the correct parameters.

## Setup

1. **Install Ollama:**
    ```sh
    curl -fsSL https://ollama.com/install.sh | sh
    ```

2. **Pull the CodeLlama model:**
    ```sh
    ollama pull codellama
    ```

3. **Install Python requirements:**
    ```sh
    pip install requests
    ```

4. **Make the scripts executable:**
    ```sh
    chmod +x /path/to/your/project/src/core/scripts/docstrings/doc_utility.py
    chmod +x /path/to/your/project/src/core/scripts/docstrings/llm_docstring_wizard.py
    ```

## Example Aliases

You can add global aliases to your `zshrc` or `bashrc` for convenience:

```sh
alias analyze-code='python3 /path/to/your/project/scripts/generic/enhance-workflow.py --analyze'
alias gen-tests='python3 /path/to/your/project/scripts/generic/enhance-workflow.py --test'
alias explain-code='python3 /path/to/your/project/scripts/generic/enhance-workflow.py --explain'
alias suggest-refactor='python3 /path/to/your/project/scripts/generic/enhance-workflow.py --refactor'
alias smart-commit='python3 /path/to/your/project/scripts/generic/enhance-workflow.py --commit'