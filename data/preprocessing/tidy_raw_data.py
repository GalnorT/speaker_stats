import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

import pandas as pd

from logger.logger import logger, setup_logging

PROJECT_ROOT = Path(__file__).parent.parent.parent
PATH_TO_INPUT_CSV = PROJECT_ROOT / "data" / "raw" / "debate_data.csv"
PATH_TO_OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "tidy_debate_data.csv"


class Side(Enum):
    AFF = "aff"
    NEG = "neg"


class InputCsvColumns(Enum):
    """Column names in the input CSV file."""
    ID = "id"
    DATE = "date"
    TOURNAMENT_ID = "tournament_id"
    TOURNAMENT_NAME = "tournament_name"
    MOTION = "motion"
    TEAMS = "teams"
    JUDGES_SCORING = "judges_scoring"


class TeamDataKeys(Enum):
    """Keys in the teams JSON data."""
    TEAM_NAME = "team_name"
    SIDE = "side"
    SPEAKERS = "speakers"


class SpeakerDataKeys(Enum):
    """Keys in the speaker data within teams."""
    NAME = "name"
    POINTS = "points"


class JudgeDataKeys(Enum):
    """Keys in the judges scoring JSON data."""
    NAME = "name"
    SIDE = "side"
    SCORE = "score"


@dataclass
class ParsedSpeaker:
    """Represents a single speaker in a debate."""

    name: str
    points: float
    position: int


@dataclass
class DebateTeam:
    """Intermediate representation of a team in a debate."""

    team_name: str
    side: Side
    speakers: list[ParsedSpeaker]


@dataclass
class ParsedDebate:
    """Intermediate representation of a full debate."""

    debate_id: int
    date: datetime
    tournament_id: int
    tournament_name: str
    motion: str
    aff_team: DebateTeam
    neg_team: DebateTeam
    ballots_aff: int
    ballots_neg: int


@dataclass
class SpeakerSpeech:
    """Represents a single speaker's speech in a debate (tidy format)."""

    debate_id: int
    date: datetime
    tournament_id: int
    tournament_name: str
    motion: str
    side: Side
    speaker_name: str
    speaker_position: int
    speaker_points: float
    ballots_gained: int
    opponent_team_name: str


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
        return json.loads(teams_str)
    except json.JSONDecodeError:
        try:
            temp_str = teams_str.replace('"', "___TEMP___")
            temp_str = temp_str.replace("'", '"')
            temp_str = temp_str.replace("___TEMP___", '\\"')
            return json.loads(temp_str)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse teams string: {teams_str[:100]}...")
            return None
    except Exception as e:
        logger.error(f"Unexpected error parsing teams string: {e}")
        return None


def parse_judges_scoring_string(judges_str: str) -> list | None:
    """Parse judges scoring string from CSV into Python list.

    Args:
        judges_str: String representation of judges scoring data

    Returns:
        Parsed list or None if parsing fails
    """
    try:
        return json.loads(judges_str)
    except json.JSONDecodeError:
        try:
            temp_str = judges_str.replace('"', "___TEMP___")
            temp_str = temp_str.replace("'", '"')
            temp_str = temp_str.replace("___TEMP___", '\\"')
            return json.loads(temp_str)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse judges string: {judges_str[:100]}...")
            return None
    except Exception as e:
        logger.error(f"Unexpected error parsing judges string: {e}")
        return None


def extract_ballots_from_judges(judges_scoring_str: str) -> dict[str, int] | None:
    """Extract ballots gained for each side from judges' decisions.

    Args:
        judges_scoring_str: JSON string with judge decisions
        Example: "[{'name': 'Kalouda Dominik', 'side': 'neg', 'score': '3:0'}]"

    Returns:
        {'aff': 0, 'neg': 3} or None if parsing fails
    """
    judges_data = parse_judges_scoring_string(judges_scoring_str)
    if judges_data is None:
        return None

    ballots_aff = 0
    ballots_neg = 0

    for judge in judges_data:
        if JudgeDataKeys.SIDE.value not in judge:
            logger.warning(f"Judge entry missing '{JudgeDataKeys.SIDE.value}': {judge}")
            continue

        winning_side = judge[JudgeDataKeys.SIDE.value].lower()
        if winning_side == Side.AFF.value:
            ballots_aff += 1
        elif winning_side == Side.NEG.value:
            ballots_neg += 1
        else:
            logger.warning(f"Unknown side in judge decision: {winning_side}")

    return {Side.AFF.value: ballots_aff, Side.NEG.value: ballots_neg}


def parse_debate_row(row: pd.Series) -> ParsedDebate | None:
    """Parse a single debate row from CSV.

    Returns None if data is malformed/invalid.

    Args:
        row: Single row from pandas DataFrame

    Returns:
        ParsedDebate object or None if parsing fails
    """
    try:
        debate_id = int(row[InputCsvColumns.ID.value])
        date = pd.to_datetime(row[InputCsvColumns.DATE.value])
        tournament_id = int(row[InputCsvColumns.TOURNAMENT_ID.value])
        tournament_name = str(row[InputCsvColumns.TOURNAMENT_NAME.value])
        motion = str(row[InputCsvColumns.MOTION.value])

        teams_data = parse_teams_string(row[InputCsvColumns.TEAMS.value])
        if teams_data is None or len(teams_data) != 2:
            logger.warning(f"Debate {debate_id}: Invalid teams data")
            return None

        ballots = extract_ballots_from_judges(row[InputCsvColumns.JUDGES_SCORING.value])
        if ballots is None:
            logger.warning(f"Debate {debate_id}: Invalid judges scoring")
            return None

        aff_team = None
        neg_team = None

        for team_data in teams_data:
            side_str = team_data.get(TeamDataKeys.SIDE.value, "").lower()
            if side_str not in [Side.AFF.value, Side.NEG.value]:
                logger.warning(f"Debate {debate_id}: Invalid side '{side_str}'")
                return None

            side = Side.AFF if side_str == Side.AFF.value else Side.NEG
            team_name = team_data.get(TeamDataKeys.TEAM_NAME.value, "")
            speakers_data = team_data.get(TeamDataKeys.SPEAKERS.value, [])

            speakers = []
            for position, speaker_data in enumerate(speakers_data, start=1):
                speaker = ParsedSpeaker(
                    name=speaker_data.get(SpeakerDataKeys.NAME.value, ""),
                    points=float(speaker_data.get(SpeakerDataKeys.POINTS.value, 0)),
                    position=position,
                )
                speakers.append(speaker)

            team = DebateTeam(team_name=team_name, side=side, speakers=speakers)

            if side == Side.AFF:
                aff_team = team
            else:
                neg_team = team

        if aff_team is None or neg_team is None:
            logger.warning(f"Debate {debate_id}: Missing aff or neg team")
            return None

        return ParsedDebate(
            debate_id=debate_id,
            date=date,
            tournament_id=tournament_id,
            tournament_name=tournament_name,
            motion=motion,
            aff_team=aff_team,
            neg_team=neg_team,
            ballots_aff=ballots[Side.AFF.value],
            ballots_neg=ballots[Side.NEG.value],
        )

    except Exception as e:
        logger.error(f"Error parsing debate row: {e}")
        return None


def debate_to_speeches(parsed_debate: ParsedDebate) -> list[SpeakerSpeech]:
    """Convert a ParsedDebate into speaker speech records.

    Creates one record per speaker with all required fields.

    Args:
        parsed_debate: Parsed debate object

    Returns:
        List of SpeakerSpeech objects (up to 6, one per speaker)
    """
    speeches = []

    # Process affirmative team
    for speaker in parsed_debate.aff_team.speakers:
        speech = SpeakerSpeech(
            debate_id=parsed_debate.debate_id,
            date=parsed_debate.date,
            tournament_id=parsed_debate.tournament_id,
            tournament_name=parsed_debate.tournament_name,
            motion=parsed_debate.motion,
            side=Side.AFF,
            speaker_name=speaker.name,
            speaker_position=speaker.position,
            speaker_points=speaker.points,
            ballots_gained=parsed_debate.ballots_aff,
            opponent_team_name=parsed_debate.neg_team.team_name,
        )
        speeches.append(speech)

    # Process negative team
    for speaker in parsed_debate.neg_team.speakers:
        speech = SpeakerSpeech(
            debate_id=parsed_debate.debate_id,
            date=parsed_debate.date,
            tournament_id=parsed_debate.tournament_id,
            tournament_name=parsed_debate.tournament_name,
            motion=parsed_debate.motion,
            side=Side.NEG,
            speaker_name=speaker.name,
            speaker_position=speaker.position,
            speaker_points=speaker.points,
            ballots_gained=parsed_debate.ballots_neg,
            opponent_team_name=parsed_debate.aff_team.team_name,
        )
        speeches.append(speech)

    return speeches


def create_tidy_dataframe(speeches: list[SpeakerSpeech]) -> pd.DataFrame:
    """Convert list of SpeakerSpeech objects to pandas DataFrame.

    Args:
        speeches: List of SpeakerSpeech objects

    Returns:
        DataFrame with tidy format data
    """
    data = {
        "debate_id": [s.debate_id for s in speeches],
        "date": [s.date for s in speeches],
        "tournament_id": [s.tournament_id for s in speeches],
        "tournament_name": [s.tournament_name for s in speeches],
        "motion": [s.motion for s in speeches],
        "side": [s.side.value for s in speeches],
        "speaker_name": [s.speaker_name for s in speeches],
        "speaker_position": [s.speaker_position for s in speeches],
        "speaker_points": [s.speaker_points for s in speeches],
        "ballots_gained": [s.ballots_gained for s in speeches],
        "opponent_team_name": [s.opponent_team_name for s in speeches],
    }

    return pd.DataFrame(data)


def process_csv_to_tidy(input_csv_path: Path, output_csv_path: Path) -> None:
    """Main pipeline: read CSV, transform to tidy format, save.

    Args:
        input_csv_path: Path to input debate CSV
        output_csv_path: Path to output tidy CSV
    """
    logger.info(f"Reading debate data from: {input_csv_path}")
    df = pd.read_csv(input_csv_path, encoding="utf-8")
    logger.info(f"Loaded {len(df)} debates")

    all_speeches = []
    malformed_count = 0

    for _, row in df.iterrows():
        parsed_debate = parse_debate_row(row)
        if parsed_debate is None:
            malformed_count += 1
            continue

        speeches = debate_to_speeches(parsed_debate)
        all_speeches.extend(speeches)

    logger.info(f"Successfully parsed {len(df) - malformed_count} debates")
    logger.info(f"Malformed debates: {malformed_count}")
    logger.info(f"Total speeches created: {len(all_speeches)}")

    tidy_df = create_tidy_dataframe(all_speeches)

    logger.info("\nData validation:")
    logger.info(f"Missing values per column:\n{tidy_df.isnull().sum()}")
    logger.info(f"\nSide distribution:\n{tidy_df['side'].value_counts()}")
    logger.info(
        f"\nSpeaker position distribution:\n{tidy_df['speaker_position'].value_counts()}"
    )

    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    tidy_df.to_csv(output_csv_path, index=False, encoding="utf-8")
    logger.info(f"\nSaved tidy data to: {output_csv_path}")


def cmd_tidy(args):
    """Command to transform debate data into tidy format."""
    input_path = Path(args.input)
    output_path = Path(args.output)

    print(f"Transforming debate data from: {input_path}")
    process_csv_to_tidy(input_path, output_path)
    print(f"Tidy data saved to: {output_path}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Transform debate data into tidy format (one speech per row)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--input",
        type=str,
        default=str(PATH_TO_INPUT_CSV),
        help=f"Path to input debate CSV (default: {PATH_TO_INPUT_CSV})",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=str(PATH_TO_OUTPUT_CSV),
        help=f"Path to output tidy CSV (default: {PATH_TO_OUTPUT_CSV})",
    )

    args = parser.parse_args()
    cmd_tidy(args)


if __name__ == "__main__":
    setup_logging()
    main()
