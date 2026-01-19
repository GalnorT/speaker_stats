"""Path constants for data preprocessing scripts."""
from pathlib import Path

# Project structure
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Directories
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
RESOURCES_DIR = PROJECT_ROOT / "data" / "resources"

# Input files
PATH_TO_INPUT_CSV = RAW_DATA_DIR / "debate_data.csv"

# Resource files
PATH_TO_MALE_NAMES = RESOURCES_DIR / "male_names.txt"
PATH_TO_FEMALE_NAMES = RESOURCES_DIR / "female_names.txt"
PATH_TO_CATEGORIES_FILE = RESOURCES_DIR / "category_keywords.json"

# Processed output files
PATH_TO_DEBATER_NAMES = PROCESSED_DATA_DIR / "debater_names.txt"
PATH_TO_GENDER_OUTPUT = PROCESSED_DATA_DIR / "debater_genders.csv"
PATH_TO_MOTIONS_LIST = PROCESSED_DATA_DIR / "motions.txt"
PATH_TO_CATEGORIZATION_OUTPUT = PROCESSED_DATA_DIR / "motion_categories.csv"
PATH_TO_TIDY_OUTPUT = PROCESSED_DATA_DIR / "tidy_debate_data.csv"