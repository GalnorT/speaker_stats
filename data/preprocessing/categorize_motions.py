import argparse
import json
import string
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from logger.logger import log_function_call, logger, setup_logging

PROJECT_ROOT = Path(__file__).parent.parent.parent
PATH_TO_INPUT_CSV = PROJECT_ROOT / "data" / "raw" / "debate_data.csv"
PATH_TO_CATEGORIES_FILE = PROJECT_ROOT / "data" / "resources" / "category_keywords.json"
PATH_TO_MOTIONS_LIST = PROJECT_ROOT / "data" / "processed" / "motions.txt"
PATH_TO_CATEGORIZATION_OUTPUT = (
    PROJECT_ROOT / "data" / "processed" / "motion_categories.csv"
)


@dataclass
class Motion:
    """Represents a debate motion."""

    text: str
    normalized_words: list[str]


@dataclass
class Category:
    """Represents a debate topic category with keywords."""

    name: str
    keywords: set[str]


@dataclass
class CategoryScore:
    """Score for a category-motion match."""

    category: Category
    score: int


@dataclass
class MotionCategorization:
    """Final categorization result for a motion."""

    motion_text: str
    top_category_1: CategoryScore | None
    top_category_2: CategoryScore | None
    top_category_3: CategoryScore | None


def normalize_text(text: str) -> str:
    """Normalize Czech text by removing diacritics and converting to lowercase.

    Args:
        text: Input text to normalize

    Returns:
        Normalized text (lowercase, no diacritics)
    """
    # Decompose Unicode characters and remove combining marks (diacritics)
    normalized = unicodedata.normalize("NFD", text)
    without_diacritics = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    return without_diacritics.lower()


def normalize_motion(motion_text: str) -> Motion:
    """Parse and normalize a motion string into words.

    Args:
        motion_text: Original motion text

    Returns:
        Motion object with normalized words
    """
    normalized_text = normalize_text(motion_text)
    words = normalized_text.split()
    clean_words = []
    for word in words:
        cleaned_word = word.strip(string.punctuation)
        if cleaned_word:
            clean_words.append(cleaned_word)
    return Motion(text=motion_text, normalized_words=clean_words)


def load_categories(categories_path: Path) -> list[Category]:
    """Load all categories from JSON file.

    Args:
        categories_path: Path to category keywords JSON file

    Returns:
        Dictionary mapping category_name -> Category object
    """
    logger.info(f"Loading categories from: {categories_path}")

    with open(categories_path, "r", encoding="utf-8") as f:
        category_data = json.load(f)

    categories: list[Category] = []
    for category_name, keywords_list in category_data.items():
        normalized_keywords = {normalize_text(keyword) for keyword in keywords_list}
        categories.append(Category(name=category_name, keywords=normalized_keywords))

    logger.info(f"Loaded {len(categories)} categories")
    return categories


def extract_motions(csv_path: Path) -> set[str]:
    """Extract unique motions from debate CSV file.

    Args:
        csv_path: Path to the input CSV file

    Returns:
        Set of unique motion texts
    """
    logger.info(f"Extracting motions from: {csv_path}")

    df = pd.read_csv(csv_path, encoding="utf-8")

    motions = set()
    for motion in df["motion"]:
        if pd.notna(motion) and motion.strip():
            motions.add(motion.strip())

    logger.info(f"Extracted {len(motions)} unique motions")
    return motions


def save_motions(motions: set[str], output_path: Path) -> None:
    """Save motions to text file.

    Args:
        motions: Set of motion texts
        output_path: Path to output text file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for motion in sorted(motions):
            f.write(f"{motion}\n")

    logger.info(f"Saved {len(motions)} motions to: {output_path}")


def load_motions(input_path: Path) -> set[str]:
    """Load motions from text file.

    Args:
        input_path: Path to input text file

    Returns:
        Set of motion texts
    """
    logger.info(f"Loading motions from: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        motions = {line.strip() for line in f if line.strip()}

    logger.info(f"Loaded {len(motions)} motions")
    return motions


@log_function_call()
def calculate_category_score(motion: Motion, category: Category) -> CategoryScore:
    """Calculate match score between motion and category.

    Args:
        motion: Motion object with normalized words
        category: Category object with keywords

    Returns:
        CategoryScore object with match count
    """
    score = 0
    motion_words_set = set(motion.normalized_words)
    matching_keywords = []

    for keyword in category.keywords:
        if keyword in motion_words_set:
            matching_keywords.append(keyword)
            score += 1

    logger.debug(
        f"Matching keywords for category '{category.name}': {matching_keywords}"
    )

    return CategoryScore(category=category, score=score)


def categorize_motion(
    motion_text: str, categories: list[Category]
) -> MotionCategorization:
    """Categorize a single motion using all available categories.

    Args:
        motion_text: Original motion text
        categories: Dictionary of available categories

    Returns:
        MotionCategorization with top 3 categories (or fewer if tied/no matches)
    """
    motion = normalize_motion(motion_text)

    scores = []
    for category in categories:
        category_score = calculate_category_score(motion, category)
        if category_score.score > 0:
            scores.append(category_score)

    scores.sort(key=lambda x: x.score, reverse=True)

    top_1 = scores[0] if len(scores) >= 1 else None
    top_2 = scores[1] if len(scores) >= 2 else None
    top_3 = scores[2] if len(scores) >= 3 else None

    return MotionCategorization(
        motion_text=motion_text,
        top_category_1=top_1,
        top_category_2=top_2,
        top_category_3=top_3,
    )


def save_categorization_results(
    results: list[MotionCategorization], output_path: Path
) -> None:
    """Save categorization results to CSV.

    Args:
        results: List of MotionCategorization objects
        output_path: Path to output CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "motion": [r.motion_text for r in results],
        "category_1": [
            r.top_category_1.category.name if r.top_category_1 else "" for r in results
        ],
        "category_1_score": [
            r.top_category_1.score if r.top_category_1 else 0 for r in results
        ],
        "category_2": [
            r.top_category_2.category.name if r.top_category_2 else "" for r in results
        ],
        "category_2_score": [
            r.top_category_2.score if r.top_category_2 else 0 for r in results
        ],
        "category_3": [
            r.top_category_3.category.name if r.top_category_3 else "" for r in results
        ],
        "category_3_score": [
            r.top_category_3.score if r.top_category_3 else 0 for r in results
        ],
    }

    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False, encoding="utf-8")

    logger.info(f"Saved categorization results to: {output_path}")


def cmd_extract_motions(args):
    """Command to extract unique motions from debate CSV."""
    setup_logging()

    input_path = Path(args.input)
    output_path = Path(args.output)

    print(f"Extracting motions from: {input_path}")
    motions = extract_motions(input_path)
    print(f"Found {len(motions)} unique motions")

    save_motions(motions, output_path)
    print(f"Saved motions to: {output_path}")


def cmd_categorize(args):
    """Command to categorize motions using category keywords."""
    setup_logging()

    motions_path = Path(args.motions_file)
    categories_path = Path(args.categories_file)
    output_path = Path(args.output)

    print(f"Loading motions from: {motions_path}")
    motions = load_motions(motions_path)
    print(f"Loaded {len(motions)} motions")

    print(f"Loading categories from: {categories_path}")
    categories = load_categories(categories_path)
    print(f"Loaded {len(categories)} categories")

    print("Categorizing motions...")
    results = []
    for motion_text in sorted(motions):
        result = categorize_motion(motion_text, categories)
        results.append(result)

    save_categorization_results(results, output_path)
    print(f"Categorization results saved to: {output_path}")

    no_category_count = sum(1 for r in results if r.top_category_1 is None)

    print("\nSummary:")
    print(f"  Total motions categorized: {len(results)}")
    print(f"  No categories: {no_category_count}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Motion categorization tool for debate motions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Extract motions command
    extract_parser = subparsers.add_parser(
        "extract", help="Extract unique motions from debate CSV"
    )
    extract_parser.add_argument(
        "-i", "--input", default=str(PATH_TO_INPUT_CSV), help="Path to input CSV file"
    )
    extract_parser.add_argument(
        "-o",
        "--output",
        default=str(PATH_TO_MOTIONS_LIST),
        help="Path to output motions text file",
    )
    extract_parser.set_defaults(func=cmd_extract_motions)

    # Categorize command
    categorize_parser = subparsers.add_parser(
        "categorize", help="Categorize motions using category keywords"
    )
    categorize_parser.add_argument(
        "-m",
        "--motions-file",
        default=str(PATH_TO_MOTIONS_LIST),
        help="Path to motions text file",
    )
    categorize_parser.add_argument(
        "-c",
        "--categories-file",
        default=str(PATH_TO_CATEGORIES_FILE),
        help="Path to category keywords JSON file",
    )
    categorize_parser.add_argument(
        "-o",
        "--output",
        default=str(PATH_TO_CATEGORIZATION_OUTPUT),
        help="Path to output CSV file",
    )
    categorize_parser.set_defaults(func=cmd_categorize)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
    else:
        args.func(args)


if __name__ == "__main__":
    main()
