import csv
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
PATH_TO_INPUT_CSV = PROJECT_ROOT / "data" / "raw" / "debate_data.csv"
PATH_TO_MALE_NAMES = PROJECT_ROOT / "data" / "resources" / "male_names.txt"
PATH_TO_FEMALE_NAMES = PROJECT_ROOT / "data" / "resources" / "female_names.txt"
PATH_TO_GENDER_OUTPUT = PROJECT_ROOT / "data" / "processed" / "debater_genders.csv"

if not PATH_TO_INPUT_CSV.exists():
    raise FileNotFoundError(f"Input file not found: {PATH_TO_INPUT_CSV}")


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


def load_name_lists() -> tuple[set[str], set[str]]:
    """Load Czech/English male and female name lists.

    Returns:
        Tuple of (male_names, female_names)
    """
    male_names = set()
    female_names = set()

    if PATH_TO_MALE_NAMES.exists():
        with open(PATH_TO_MALE_NAMES, "r", encoding="utf-8") as f:
            male_names = {line.strip().lower() for line in f if line.strip()}

    if PATH_TO_FEMALE_NAMES.exists():
        with open(PATH_TO_FEMALE_NAMES, "r", encoding="utf-8") as f:
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


def main():
    """Main preprocessing pipeline for gender guessing."""
    male_names, female_names = load_name_lists()

    debater_names = extract_debater_names(PATH_TO_INPUT_CSV)
    print(f"Extracted {len(debater_names)} unique debater names")

    results = []
    for name in sorted(debater_names):
        result = guess_gender(name, male_names, female_names)
        results.append(result)

    save_gender_results(results, PATH_TO_GENDER_OUTPUT)
    print(f"Gender results saved to {PATH_TO_GENDER_OUTPUT}")

    male_count = sum(1 for r in results if r.gender == Gender.MALE)
    female_count = sum(1 for r in results if r.gender == Gender.FEMALE)
    inconclusive_count = sum(1 for r in results if r.gender == Gender.INCONCLUSIVE)

    print("\nSummary:")
    print(f"  Male: {male_count}")
    print(f"  Female: {female_count}")
    print(f"  Inconclusive: {inconclusive_count}")


if __name__ == "__main__":
    main()
