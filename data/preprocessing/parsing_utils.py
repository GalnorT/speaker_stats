"""Utilities for parsing JSON strings from CSV data."""
import json

from logger.logger import logger

TEMPORARY_REPLACEMENT_STRING = "___TEMP___"


def parse_teams_string(teams_str: str) -> list | None:
    """Parse teams string from CSV into Python list.

    Required to handle name strings with nicknames containing quotes.
    E.g. {'name': 'Novák "Speedy" Jakub'}

    Args:
        teams_str: String representation of teams data

    Returns:
        Parsed list or None if parsing fails
    """
    try:
        teams_str = teams_str.replace('"', TEMPORARY_REPLACEMENT_STRING)
        teams_str = teams_str.replace("'", '"')
        teams_str = teams_str.replace("None", "null")
        teams = json.loads(teams_str)

        for team in teams:
            for speaker in team["speakers"]:
                if speaker["name"]:
                    speaker["name"] = speaker["name"].replace(
                        TEMPORARY_REPLACEMENT_STRING, '"'
                    )
        return teams
    except json.JSONDecodeError:
        return None
    except Exception as e:
        logger.error(f"Unexpected error while parsing teams string: {e}")
        logger.debug(f"Teams string: {teams_str}")
        raise e


def parse_judges_scoring_string(judges_str: str) -> list | None:
    """Parse judges scoring string from CSV into Python list.

    Args:
        judges_str: String representation of judges scoring data

    Returns:
        Parsed list or None if parsing fails
    """
    try:
        judges_str = judges_str.replace("'", '"')
        judges_str = judges_str.replace("None", "null")
        return json.loads(judges_str)
    except json.JSONDecodeError:
        return None
    except Exception as e:
        logger.error(f"Unexpected error while parsing judges string: {e}")
        logger.debug(f"Judges string: {judges_str}")
        raise e