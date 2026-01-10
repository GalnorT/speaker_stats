import argparse
import csv
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
PATH_TO_INPUT_CSV = PROJECT_ROOT / "data" / "raw" / "debate_data.csv"
PATH_TO_MALE_NAMES = PROJECT_ROOT / "data" / "resources" / "male_names.txt"
PATH_TO_FEMALE_NAMES = PROJECT_ROOT / "data" / "resources" / "female_names.txt"
PATH_TO_DEBATER_NAMES = PROJECT_ROOT / "data" / "processed" / "debater_names.txt"
PATH_TO_GENDER_OUTPUT = PROJECT_ROOT / "data" / "processed" / "debater_genders.csv"


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"
    INCONCLUSIVE = "inconclusive"


class GenderGuessMethod(Enum):
    LASTNAME_SUFFIX = "lastname_suffix"
    FIRSTNAME_MATCH = "firstname_match"
    INCONCLUSIVE = "inconclusive"


@dataclass
class DebaterName:
    full_name: str
    first_name: str
    last_name: str


@dataclass
class GenderGuess:
    debater_name: DebaterName
    gender: Gender
    method_used: GenderGuessMethod


CZECH_FEMALE_SUFFIXES = ["ová", "á"]


def extract_debater_names(csv_path: Path) -> set[str]:
    """Extract unique debater names from the debate CSV file.

    Args:
        csv_path: Path to the input CSV file

    Returns:
        Set of unique debater names
    """
    debater_names = set()

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            teams = json.loads(row["teams"])
            for team in teams:
                for speaker in team["speakers"]:
                    debater_names.add(speaker["name"])

    return debater_names


def save_debater_names(names: set[str], output_path: Path) -> None:
    """Save debater names to a text file.

    Args:
        names: Set of debater names
        output_path: Path to output text file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for name in sorted(names):
            f.write(f"{name}\n")


def load_debater_names(input_path: Path) -> set[str]:
    """Load debater names from a text file.

    Args:
        input_path: Path to input text file

    Returns:
        Set of debater names
    """
    with open(input_path, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def parse_name(full_name: str) -> DebaterName:
    """Split full name into first and last name.

    Args:
        full_name: Full name string (e.g., "Novák Jakub")

    Returns:
        DebaterName object with parsed components
    """
    parts = full_name.strip().split()

    if len(parts) >= 2:
        last_name = parts[0]
        first_name = parts[1]
    else:
        last_name = parts[0] if parts else ""
        first_name = ""

    return DebaterName(full_name=full_name, first_name=first_name, last_name=last_name)


def guess_gender_from_lastname(last_name: str) -> Gender | None:
    """Check if lastname ends with Czech female suffixes.

    Args:
        last_name: Last name to check

    Returns:
        Gender.FEMALE if matches suffix, None otherwise
    """
    last_name_lower = last_name.lower()

    for suffix in CZECH_FEMALE_SUFFIXES:
        if last_name_lower.endswith(suffix):
            return Gender.FEMALE

    return None


def guess_gender_from_firstname(
    first_name: str, male_names: set[str], female_names: set[str]
) -> Gender:
    """Match first name against name lists.

    Args:
        first_name: First name to check
        male_names: Set of male first names
        female_names: Set of female first names

    Returns:
        Gender enum value
    """
    first_name_lower = first_name.lower().strip()

    is_female = first_name_lower in female_names
    is_male = first_name_lower in male_names

    if is_female and not is_male:
        return Gender.FEMALE
    elif is_male and not is_female:
        return Gender.MALE
    else:
        return Gender.INCONCLUSIVE


def guess_gender(
    full_name: str, male_names: set[str], female_names: set[str]
) -> GenderGuess:
    """Main gender guessing function using 2-step approach.

    Args:
        full_name: Full debater name
        male_names: Set of male first names
        female_names: Set of female first names

    Returns:
        GenderGuess object with results
    """
    debater_name = parse_name(full_name)

    gender_from_lastname = guess_gender_from_lastname(debater_name.last_name)
    if gender_from_lastname == Gender.FEMALE:
        return GenderGuess(
            debater_name=debater_name,
            gender=Gender.FEMALE,
            method_used=GenderGuessMethod.LASTNAME_SUFFIX,
        )

    gender_from_firstname = guess_gender_from_firstname(
        debater_name.first_name, male_names, female_names
    )

    if gender_from_firstname != Gender.INCONCLUSIVE:
        return GenderGuess(
            debater_name=debater_name,
            gender=gender_from_firstname,
            method_used=GenderGuessMethod.FIRSTNAME_MATCH,
        )

    return GenderGuess(
        debater_name=debater_name,
        gender=Gender.INCONCLUSIVE,
        method_used=GenderGuessMethod.INCONCLUSIVE,
    )


def load_name_lists(
    male_names_path: Path, female_names_path: Path
) -> tuple[set[str], set[str]]:
    """Load Czech/English male and female name lists.

    Args:
        male_names_path: Path to male names file
        female_names_path: Path to female names file

    Returns:
        Tuple of (male_names, female_names)
    """
    male_names = set()
    female_names = set()

    if male_names_path.exists():
        with open(male_names_path, "r", encoding="utf-8") as f:
            male_names = {line.strip().lower() for line in f if line.strip()}

    if female_names_path.exists():
        with open(female_names_path, "r", encoding="utf-8") as f:
            female_names = {line.strip().lower() for line in f if line.strip()}

    return male_names, female_names


def save_gender_results(results: list[GenderGuess], output_path: Path) -> None:
    """Save gender guessing results to CSV.

    Args:
        results: List of GenderGuess objects
        output_path: Path to output CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["debater_name", "is_male", "inconclusive", "method_used"])

        for result in results:
            writer.writerow(
                [
                    result.debater_name.full_name,
                    result.gender == Gender.MALE,
                    result.gender == Gender.INCONCLUSIVE,
                    result.method_used.value,
                ]
            )


def cmd_extract_names(args):
    """Command to extract debater names from debate CSV."""
    input_path = Path(args.input)
    output_path = Path(args.output)

    print(f"Extracting names from: {input_path}")
    debater_names = extract_debater_names(input_path)
    print(f"Found {len(debater_names)} unique debater names")

    save_debater_names(debater_names, output_path)
    print(f"Saved debater names to: {output_path}")


def cmd_analyze(args):
    """Command to analyze debater names and guess genders."""
    debater_names_path = Path(args.debater_names_file)
    male_names_path = Path(args.male_names_file)
    female_names_path = Path(args.female_names_file)
    output_path = Path(args.output)

    print(f"Loading debater names from: {debater_names_path}")
    debater_names = load_debater_names(debater_names_path)
    print(f"Loaded {len(debater_names)} debater names")

    print("Loading name lists...")
    male_names, female_names = load_name_lists(male_names_path, female_names_path)
    print(f"  Male names: {len(male_names)}")
    print(f"  Female names: {len(female_names)}")

    print("Analyzing genders...")
    results = []
    for name in sorted(debater_names):
        result = guess_gender(name, male_names, female_names)
        results.append(result)

    save_gender_results(results, output_path)
    print(f"Gender results saved to: {output_path}")

    male_count = sum(1 for r in results if r.gender == Gender.MALE)
    female_count = sum(1 for r in results if r.gender == Gender.FEMALE)
    inconclusive_count = sum(1 for r in results if r.gender == Gender.INCONCLUSIVE)

    print("\nSummary:")
    print(f"  Male: {male_count}")
    print(f"  Female: {female_count}")
    print(f"  Inconclusive: {inconclusive_count}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Gender estimation tool for debater names",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # extract-names command
    extract_parser = subparsers.add_parser(
        "extract-names", help="Extract debater names from debate CSV"
    )
    extract_parser.add_argument(
        "-i",
        "--input",
        type=str,
        default=str(PATH_TO_INPUT_CSV),
        help=f"Input CSV file path (default: {PATH_TO_INPUT_CSV})",
    )
    extract_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=str(PATH_TO_DEBATER_NAMES),
        help=f"Output text file path (default: {PATH_TO_DEBATER_NAMES})",
    )

    # analyze command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze debater names and guess genders"
    )
    analyze_parser.add_argument(
        "-d",
        "--debater-names-file",
        type=str,
        default=str(PATH_TO_DEBATER_NAMES),
        help=f"Debater names file path (default: {PATH_TO_DEBATER_NAMES})",
    )
    analyze_parser.add_argument(
        "-m",
        "--male-names-file",
        type=str,
        default=str(PATH_TO_MALE_NAMES),
        help=f"Male names file path (default: {PATH_TO_MALE_NAMES})",
    )
    analyze_parser.add_argument(
        "-f",
        "--female-names-file",
        type=str,
        default=str(PATH_TO_FEMALE_NAMES),
        help=f"Female names file path (default: {PATH_TO_FEMALE_NAMES})",
    )
    analyze_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=str(PATH_TO_GENDER_OUTPUT),
        help=f"Output CSV file path (default: {PATH_TO_GENDER_OUTPUT})",
    )

    args = parser.parse_args()

    if args.command == "extract-names":
        cmd_extract_names(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
