import json
import os

def load_test_data(file_name: str) -> list:
    """
    Loads JSON data from the data directory.
    Returns a list of dictionaries for pytest parameterization.
    """
    # Navigate up from utils/ to the project root, then into data/
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, 'data', file_name)

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)