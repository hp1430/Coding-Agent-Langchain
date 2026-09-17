from tools.paths import resolve_work_path
from langchain.tools import tool

@tool
def read_file(path: str) -> str:
    """
        Reads a UTF-8 encoded text file from the working directory.
        Args:
            path: Relative path of the file to read. E.g. 'src/App.js' or 'README.md' or 'data/example.json'.
        Returns the content of the file as a string.
    """

    try:
        file_path = resolve_work_path(path)    # We are checking if the path is a valid path inside the working directory -> workspace of not
    except ValueError as err:
        return f"Path escapes working directory: {err}"

    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"File not found: {file_path}"
    except PermissionError:
        return f"Permission denied: {file_path}"
    except Exception as err:
        return f"Error reading file {file_path}: {err}"
