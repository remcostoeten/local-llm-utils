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
    python llm_docstring_wizard.py --find "modal component" --generate-docs
    ```
