# Python Jupyter Environment

This project uses `uv` for Python package management and Jupyter notebooks for development.

## Setup

1. Make sure you have `uv` installed. If not, install it following the instructions at https://github.com/astral-sh/uv

2. Create and activate the virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```

## Using Jupyter Notebooks

1. Start Jupyter Notebook:
   ```bash
   jupyter notebook
   ```

2. Your browser should open automatically to the Jupyter interface. If not, copy and paste the URL from the terminal output.

3. Navigate to the `notebooks` directory to create or open notebooks.

## Project Structure

- `notebooks/`: Directory containing Jupyter notebooks
- `requirements.txt`: Python package dependencies
- `.venv/`: Virtual environment directory (not tracked in git) 