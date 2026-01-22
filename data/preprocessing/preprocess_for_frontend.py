"""Transform debate data into frontend-ready JSON format with speaker statistics."""

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import pandas as pd

from constants import PATH_TO_FINAL_OUTPUT, PATH_TO_SPEAKER_STATS_OUTPUT, Side
from logger.logger import logger, setup_logging


class InputColumns(Enum):
    """Column names in the input CSV file."""

    SPEAKER_NAME = "speaker_name"
    SIDE = "side"
    BALLOTS_GAINED = "ballots_gained"
    SPEAKER_POSITION = "speaker_position"
    SPEAKER_POINTS = "speaker_points"
    CATEGORY_1 = "category_1"
    DEBATE_DATE = "debate_date"


class OutputFields(Enum):
    """Field names in the output JSON."""

    NAME = "name"
    SIDE_WIN_RATES = "side_win_rates"
    POSITIONS_SPEAKER_POINTS = "positions_speaker_points"
    MOTION_CATEGORY_STATS = "motion_category_stats"
    DEBATES = "debates"

    # Nested fields
    TOTAL = "total"
    AFF = "aff"
    NEG = "neg"
    TOP_3 = "top_3"
    BOTTOM_3 = "bottom_3"
    CATEGORY = "category"
    WIN_RATE = "win_rate"
    DEBATES_COUNT = "debates"
    DATE = "date"


@dataclass
class CategoryStats:
    debates: int = 0
    wins: int = 0


@dataclass
class SpeakerStats:
    """Statistics for a single speaker."""

    name: str
    total_debates: int = 0
    total_wins: int = 0
    aff_debates: int = 0
    aff_wins: int = 0
    neg_debates: int = 0
    neg_wins: int = 0
    position_points: dict = field(default_factory=lambda: defaultdict(list))
    #pylint: disable=unnecessary-lambda
    category_stats: dict = field(default_factory=lambda: defaultdict(lambda: CategoryStats()))
    debates: list = field(default_factory=list)


def remove_nickname(name: str) -> str:
    """Remove nickname in quotes from speaker name.

    Args:
        name: Speaker name possibly containing nickname like 'Novák "Speedy" Jakub'

    Returns:
        Name without nickname: 'Novák Jakub'
    """
    cleaned = re.sub(r'"[^"]*"', "", name)
    cleaned = " ".join(cleaned.split())
    return cleaned.strip()


def is_win(ballots_gained: float) -> bool:
    """Check if speaker won the debate.

    Args:
        ballots_gained: Number of ballots gained

    Returns:
        True if ballots >= 2 (win), False otherwise
    """
    return ballots_gained >= 2


def calculate_win_rate(wins: int, total: int) -> float:
    """Calculate win rate rounded to 2 decimal places.

    Args:
        wins: Number of wins
        total: Total number of debates

    Returns:
        Win rate as float (0.0 to 1.0), or 0.0 if no debates
    """
    if total == 0:
        return 0.0
    return round(wins / total, 2)


def process_speaker_data(df: pd.DataFrame) -> dict[str, SpeakerStats]:
    """Process dataframe and aggregate statistics per speaker.

    Args:
        df: DataFrame with debate data

    Returns:
        Dictionary mapping speaker name to their statistics
    """
    speakers = {}

    for _, row in df.iterrows():
        raw_name = row[InputColumns.SPEAKER_NAME.value]
        clean_name = remove_nickname(raw_name)

        if clean_name not in speakers:
            speakers[clean_name] = SpeakerStats(name=clean_name)

        speaker = speakers[clean_name]
        side = row[InputColumns.SIDE.value]
        ballots = row[InputColumns.BALLOTS_GAINED.value]
        position = int(row[InputColumns.SPEAKER_POSITION.value])
        points = row[InputColumns.SPEAKER_POINTS.value]
        category = row[InputColumns.CATEGORY_1.value]
        debate_date = row[InputColumns.DEBATE_DATE.value]

        speaker.total_debates += 1

        won = is_win(ballots)
        if won:
            speaker.total_wins += 1

        if side == Side.AFF.value:
            speaker.aff_debates += 1
            if won:
                speaker.aff_wins += 1
        elif side == Side.NEG.value:
            speaker.neg_debates += 1
            if won:
                speaker.neg_wins += 1

        if pd.notna(points):
            speaker.position_points[position].append(points)

        if pd.notna(category) and category != "":
            speaker.category_stats[category].debates += 1
            if won:
                speaker.category_stats[category].wins += 1

        if pd.notna(debate_date):
            speaker.debates.append(
                {OutputFields.DATE.value: str(debate_date).split()[0]}
            )

    return speakers


def calculate_side_win_rates(speaker: SpeakerStats, has_results: bool) -> dict:
    """Calculate win rates for total, aff, and neg sides.

    Args:
        speaker: SpeakerStats object
        has_results: Whether the speaker has any wins or losses

    Returns:
        Dictionary with side win rates
    """
    side_win_rates = {}

    if has_results:
        side_win_rates[OutputFields.TOTAL.value] = calculate_win_rate(
            speaker.total_wins, speaker.total_debates
        )
        if speaker.aff_debates > 0:
            side_win_rates[OutputFields.AFF.value] = calculate_win_rate(
                speaker.aff_wins, speaker.aff_debates
            )
        if speaker.neg_debates > 0:
            side_win_rates[OutputFields.NEG.value] = calculate_win_rate(
                speaker.neg_wins, speaker.neg_debates
            )

    return side_win_rates


def calculate_positions_speaker_points(speaker: SpeakerStats) -> dict:
    """Calculate average speaker points per position.

    Args:
        speaker: SpeakerStats object

    Returns:
        Dictionary mapping position (as string) to average points
    """
    positions_speaker_points = {}

    for position in [1, 2, 3]:
        if position in speaker.position_points and speaker.position_points[position]:
            avg_points = sum(speaker.position_points[position]) / len(
                speaker.position_points[position]
            )
            positions_speaker_points[str(position)] = round(avg_points, 2)
        else:
            positions_speaker_points[str(position)] = 0.0

    return positions_speaker_points


def calculate_motion_category_stats(speaker: SpeakerStats, has_results: bool) -> dict:
    """Calculate motion category statistics (top 3 and bottom 3).

    Args:
        speaker: SpeakerStats object
        has_results: Whether the speaker has any wins or losses

    Returns:
        Dictionary with top_3 and bottom_3 category statistics
    """
    motion_category_stats = {
        OutputFields.TOP_3.value: [],
        OutputFields.BOTTOM_3.value: [],
    }

    if has_results and speaker.category_stats:
        category_win_rates = []

        for category, stats in speaker.category_stats.items():
            if stats.debates > 0:
                win_rate = calculate_win_rate(stats.wins, stats.debates)
                category_win_rates.append(
                    {
                        OutputFields.CATEGORY.value: category,
                        OutputFields.WIN_RATE.value: win_rate,
                        OutputFields.DEBATES_COUNT.value: stats.debates,
                    }
                )

        category_win_rates.sort(
            key=lambda x: x[OutputFields.WIN_RATE.value], reverse=True
        )

        motion_category_stats[OutputFields.TOP_3.value] = category_win_rates[:3]
        motion_category_stats[OutputFields.BOTTOM_3.value] = category_win_rates[-3:][
            ::-1
        ]

    return motion_category_stats


def speaker_to_json_dict(speaker: SpeakerStats) -> dict:
    """Convert SpeakerStats to JSON-serializable dictionary.

    Args:
        speaker: SpeakerStats object

    Returns:
        Dictionary matching the frontend JSON format
    """
    has_results = speaker.total_wins > 0 or speaker.total_debates > speaker.total_wins

    side_win_rates = calculate_side_win_rates(speaker, has_results)
    positions_speaker_points = calculate_positions_speaker_points(speaker)
    motion_category_stats = calculate_motion_category_stats(speaker, has_results)

    return {
        OutputFields.NAME.value: speaker.name,
        OutputFields.SIDE_WIN_RATES.value: side_win_rates,
        OutputFields.POSITIONS_SPEAKER_POINTS.value: positions_speaker_points,
        OutputFields.MOTION_CATEGORY_STATS.value: motion_category_stats,
        OutputFields.DEBATES.value: speaker.debates,
    }


def generate_frontend_json(input_csv_path: Path, output_json_path: Path) -> None:
    """Main pipeline: read CSV, calculate stats, save JSON.

    Args:
        input_csv_path: Path to final_joined_data.csv
        output_json_path: Path to output JSON file
    """
    logger.info(f"Reading debate data from: {input_csv_path}")
    df = pd.read_csv(input_csv_path, encoding="utf-8")
    logger.info(f"Loaded {len(df)} speech records")

    speakers = process_speaker_data(df)
    logger.info(f"Processed statistics for {len(speakers)} unique speakers")

    speakers = {
        name: stats for name, stats in speakers.items() if stats.total_debates > 0
    }
    logger.info(f"Speakers with at least one debate: {len(speakers)}")

    output_data = [speaker_to_json_dict(stats) for stats in speakers.values()]

    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)

    logger.info(f"Saved frontend JSON to: {output_json_path}")
    logger.info(f"Total speakers in output: {len(output_data)}")


def cmd_preprocess(args):
    """Command to generate frontend JSON from processed data."""
    input_path = Path(args.input)
    output_path = Path(args.output)

    print(f"Generating frontend JSON from: {input_path}")
    generate_frontend_json(input_path, output_path)
    print(f"Frontend JSON saved to: {output_path}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate frontend-ready JSON with speaker statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--input",
        type=str,
        default=str(PATH_TO_FINAL_OUTPUT),
        help=f"Path to input {PATH_TO_FINAL_OUTPUT} (default: {PATH_TO_FINAL_OUTPUT})",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=str(PATH_TO_SPEAKER_STATS_OUTPUT),
        help=f"Path to output JSON file (default: {PATH_TO_SPEAKER_STATS_OUTPUT})",
    )

    args = parser.parse_args()
    cmd_preprocess(args)


if __name__ == "__main__":
    setup_logging()
    main()
