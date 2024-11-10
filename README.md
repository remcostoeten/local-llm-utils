## Local LLM utilities

Just some tools, scripts, knowledge for local development to enhance productivity.

## Contents

`/scripts/docstring`

## Script usage documentation

- Docstrings refer to `/scripts/docstrings/README.md`

## Initial local setup (PopOS)

- Install `Ollama` local (all round great coding AI model)
`curl -fsSL https://ollama.com/install.sh | sh`

- Pull the CodeLlama model (good for code related task)
`ollama pull codellama`

- Install python requirements
`pip install requests`

That's the setup done. Now we'll have to get specific. Example I will use is the `scripts/docstrings` which is an interactive CLI script to add docstrings to a file.

- Save the original script in your projects. I'll use `src/core/scripts/docstring`. Run `cp ./scrips/docstrings//doc_utillity.py ~/path/to/your/project/src/core/scripts/docstrings`.
- Save the LLM helper script tailored to the docstring specific in the same directory. So `cp ./scripts/docstrings/llm_docstring_wizard.py ~/path/to/project/src/core/scripts/docstrings`.
- Make it executabele `chmod +x /path/to/your/project/src/core/scripts/docstrings/llm_docstring_wizard.py`
- Now you can use it in several ways.

Navigate to thee root of your project
- Find and document a file based on description:
`src/core/scrips/docstrings/llm_docstring_wizard.py --find "button component" --description "Custom buttonn component" --generate-example`

- Just find a file:
`src/core/scripts/docstrings/llm_docstring_wizard.py --find "auth form component"`

- Find a file and add generated example:
`src/core/scripts/docstrings/llm_docstring_wizard.py --find "modal component" --generate-example`

The script will:

1. Use the LLM to find the most relevant TypeScript file based on your description
2. Generate appropriate examples if requested
3. Call your original doc_utility.py with the correct parameters


The `CodeLlama` model is about `4GB` and works well for code tasks. You can also try smaller models like orca-mini if you need something lighter.

## Different models to consider

```shell
# Code-specialized models
ollama pull codellama       # Best for code tasks, 4GB
ollama pull wizardcoder    # Good balance of size/performance
ollama pull deepseek-coder # Excellent for Python

# Smaller, general-purpose models
ollama pull mistral        # Great all-rounder, 4GB
ollama pull orca-mini      # Lightweight, 4GB
ollama pull neural-chat    # Fast, good for chat-like interactions

# Specialized models
ollama pull sqlcoder      # Great for database queries
ollama pull starcoder     # Good for GitHub-style code
```

## Generic local LLM script helper 

There is a generic LLM script not so case-specific over at `/scripts/generic/enhance-workflow.py`

## Usage

Simoply run the script with executing a parameter flag of one of these below

```mdx
--analyze
--test
--explain
--refactor
--commit`

Thus running (from the root here) `scripts/generic/enhance-workflow.py` and adding the parameter like `python3 generic/enhance-workflow.py --analyze src/components/Button.tsx`

One could add global `zshrc` or `bashrc` aliasses like so:

```shell
alias analyze-code='python3 dev_llm_tools.py --analyze'
alias gen-tests='python3 dev_llm_tools.py --test'
alias explain-code='python3 dev_llm_tools.py --explain'
alias suggest-refactor='python3 dev_llm_tools.py --refactor'
alias smart-commit='python3 dev_llm_tools.py --commit'
```

Make sure to insert proper path to where the file is stored. E.g. `alias explain-code='python3 ~/code/local-llm-utils/scripts/generic/enhance-workflow.py --explain`

## Performance tips

# Run Ollama with GPU support
ollama serve --gpu

# Use different models for different tasks:
- codellama: Code analysis, generation
- mistral: Documentation, explanations
- orca-mini: Quick responses

# Running an installed model
To run an installed model, use the following command:
```shell
ollama run <model-name>

## List out all intallled models

`ollama list`