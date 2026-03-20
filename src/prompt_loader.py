"""
Utility module to load prompts from the file system directory structure
"""

import os
import json
from pathlib import Path

# Get the directory where this file is located, then go up one level to find prompts/
BASE_DIR = Path(__file__).parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"

def get_category_folders():
    """Get all category folders from the prompts directory"""
    if not PROMPTS_DIR.exists():
        return []
    return [d.name for d in PROMPTS_DIR.iterdir() if d.is_dir()]

def load_prompt_file(file_path):
    """Load a single prompt JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def load_prompts_from_category(category):
    """Load all prompts from a specific category folder"""
    category_path = PROMPTS_DIR / category
    if not category_path.exists():
        return []
    
    prompts = []
    for file_path in category_path.glob("*.json"):
        prompt_data = load_prompt_file(file_path)
        if prompt_data:
            prompt_data['category'] = category
            prompts.append(prompt_data)
    
    return prompts

def get_all_prompts():
    """Load all prompts from all categories"""
    all_prompts = []
    categories = get_category_folders()
    
    for category in categories:
        prompts = load_prompts_from_category(category)
        all_prompts.extend(prompts)
    
    return all_prompts

def get_prompts_database():
    """Get prompts organized by category (for backward compatibility)"""
    database = {}
    categories = get_category_folders()
    
    for category in categories:
        database[category] = load_prompts_from_category(category)
    
    return database

def save_prompt(category, title, prompt_text, tags=None, description=None):
    """Save a new prompt to a JSON file"""
    category_path = PROMPTS_DIR / category
    category_path.mkdir(parents=True, exist_ok=True)
    
    # Create safe filename from title
    safe_filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_filename = safe_filename.replace(' ', '-').lower()
    file_path = category_path / f"{safe_filename}.json"
    
    prompt_data = {
        "title": title,
        "prompt": prompt_text,
        "tags": tags or [],
        "description": description or ""
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(prompt_data, f, indent=2, ensure_ascii=False)
    
    return file_path


