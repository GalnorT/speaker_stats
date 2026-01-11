from datetime import datetime

import pandas as pd

from data.preprocessing.tidy_raw_data import (DebateTeam, InputCsvColumns,
                                              JudgeDataKeys, ParsedDebate,
                                              ParsedSpeaker, Side,
                                              SpeakerDataKeys, TeamDataKeys,
                                              debate_to_speeches,
                                              extract_ballots_from_judges,
                                              fix_side_swap_if_needed,
                                              parse_debate_row,
                                              parse_judges_scoring_string)


class TestParseJudgesScoringString:
    def test_valid_single_judge(self):
        judges_str = f"""[
            {{
                '{JudgeDataKeys.NAME.value}': 'Judge One',
                '{JudgeDataKeys.SIDE.value}': 'aff',
                '{JudgeDataKeys.SCORE.value}': '3:0'
            }}
        ]"""
        result = parse_judges_scoring_string(judges_str)
        assert result == [
            {
                JudgeDataKeys.NAME.value: "Judge One",
                JudgeDataKeys.SIDE.value: "aff",
                JudgeDataKeys.SCORE.value: "3:0",
            }
        ]

    def test_valid_multiple_judges(self):
        judges_str = f"""[
            {{
                '{JudgeDataKeys.NAME.value}': 'Judge One',
                '{JudgeDataKeys.SIDE.value}': 'aff',
                '{JudgeDataKeys.SCORE.value}': '3:0'
            }},
            {{
                '{JudgeDataKeys.NAME.value}': 'Judge Two',
                '{JudgeDataKeys.SIDE.value}': 'neg',
                '{JudgeDataKeys.SCORE.value}': '3:0'
            }}
        ]"""
        result = parse_judges_scoring_string(judges_str)
        assert len(result) == 2
        assert result[0][JudgeDataKeys.SIDE.value] == "aff"
        assert result[1][JudgeDataKeys.SIDE.value] == "neg"

    def test_malformed_json(self):
        judges_str = "[{invalid json}]"
        result = parse_judges_scoring_string(judges_str)
        assert result is None

    def test_empty_list(self):
        judges_str = "[]"
        result = parse_judges_scoring_string(judges_str)
        assert result == []

    def test_single_quotes_conversion(self):
        judges_str = f"""[
            {{
                '{JudgeDataKeys.NAME.value}': 'Judge One',
                '{JudgeDataKeys.SIDE.value}': 'aff'
            }}
        ]"""
        result = parse_judges_scoring_string(judges_str)
        assert result is not None
        assert result[0][JudgeDataKeys.NAME.value] == "Judge One"


class TestExtractBallotsFromJudges:
    def test_single_judge_voting_aff_unanimous(self):
        judges_str = f"""[
            {{
                '{JudgeDataKeys.NAME.value}': 'Judge One',
                '{JudgeDataKeys.SIDE.value}': 'aff',
                '{JudgeDataKeys.SCORE.value}': '3:0'
            }}
        ]"""
        result = extract_ballots_from_judges(judges_str)
        assert result == {"aff": 3, "neg": 0}

    def test_single_judge_voting_neg_unanimous(self):
        judges_str = f"""[
            {{
                '{JudgeDataKeys.NAME.value}': 'Judge One',
                '{JudgeDataKeys.SIDE.value}': 'neg',
                '{JudgeDataKeys.SCORE.value}': '3:0'
            }}
        ]"""
        result = extract_ballots_from_judges(judges_str)
        assert result == {"aff": 0, "neg": 3}

    def test_single_judge_split_decision_2_1_aff(self):
        judges_str = f"""[
            {{
                '{JudgeDataKeys.NAME.value}': 'Judge One',
                '{JudgeDataKeys.SIDE.value}': 'aff',
                '{JudgeDataKeys.SCORE.value}': '2:1'
            }}
        ]"""
        result = extract_ballots_from_judges(judges_str)
        assert result == {"aff": 2, "neg": 1}

    def test_single_judge_split_decision_2_1_neg(self):
        judges_str = f"""[
            {{
                '{JudgeDataKeys.NAME.value}': 'Judge One',
                '{JudgeDataKeys.SIDE.value}': 'neg',
                '{JudgeDataKeys.SCORE.value}': '2:1'
            }}
        ]"""
        result = extract_ballots_from_judges(judges_str)
        assert result == {"aff": 1, "neg": 2}

    def test_multiple_judges_split_decision_2_1_aff(self):
        judges_str = f"""[
            {{'{JudgeDataKeys.NAME.value}': 'J1', '{JudgeDataKeys.SIDE.value}': 'aff'}},
            {{'{JudgeDataKeys.NAME.value}': 'J2', '{JudgeDataKeys.SIDE.value}': 'aff'}},
            {{'{JudgeDataKeys.NAME.value}': 'J3', '{JudgeDataKeys.SIDE.value}': 'neg'}}
        ]"""
        result = extract_ballots_from_judges(judges_str)
        assert result == {"aff": 2, "neg": 1}

    def test_multiple_judges_split_decision_2_1_neg(self):
        judges_str = f"""[
            {{'{JudgeDataKeys.NAME.value}': 'J1', '{JudgeDataKeys.SIDE.value}': 'neg'}},
            {{'{JudgeDataKeys.NAME.value}': 'J2', '{JudgeDataKeys.SIDE.value}': 'neg'}},
            {{'{JudgeDataKeys.NAME.value}': 'J3', '{JudgeDataKeys.SIDE.value}': 'aff'}}
        ]"""
        result = extract_ballots_from_judges(judges_str)
        assert result == {"aff": 1, "neg": 2}

    def test_multiple_judges_unanimous_aff(self):
        judges_str = f"""[
            {{'{JudgeDataKeys.NAME.value}': 'J1', '{JudgeDataKeys.SIDE.value}': 'aff'}},
            {{'{JudgeDataKeys.NAME.value}': 'J2', '{JudgeDataKeys.SIDE.value}': 'aff'}},
            {{'{JudgeDataKeys.NAME.value}': 'J3', '{JudgeDataKeys.SIDE.value}': 'aff'}}
        ]"""
        result = extract_ballots_from_judges(judges_str)
        assert result == {"aff": 3, "neg": 0}

    def test_multiple_judges_unanimous_neg(self):
        judges_str = f"""[
            {{'{JudgeDataKeys.NAME.value}': 'J1', '{JudgeDataKeys.SIDE.value}': 'neg'}},
            {{'{JudgeDataKeys.NAME.value}': 'J2', '{JudgeDataKeys.SIDE.value}': 'neg'}},
            {{'{JudgeDataKeys.NAME.value}': 'J3', '{JudgeDataKeys.SIDE.value}': 'neg'}}
        ]"""
        result = extract_ballots_from_judges(judges_str)
        assert result == {"aff": 0, "neg": 3}

    def test_judge_missing_side_field(self):
        judges_str = f"""[
            {{'{JudgeDataKeys.NAME.value}': 'J1', '{JudgeDataKeys.SIDE.value}': 'aff'}},
            {{'{JudgeDataKeys.NAME.value}': 'J2'}},
            {{'{JudgeDataKeys.NAME.value}': 'J3', '{JudgeDataKeys.SIDE.value}': 'neg'}}
        ]"""
        result = extract_ballots_from_judges(judges_str)
        # Should skip J2 and count J1 and J3
        assert result == {"aff": 1, "neg": 1}

    def test_invalid_side_value(self):
        judges_str = f"""[
            {{'{JudgeDataKeys.NAME.value}': 'J1', '{JudgeDataKeys.SIDE.value}': 'aff'}},
            {{'{JudgeDataKeys.NAME.value}': 'J2', '{JudgeDataKeys.SIDE.value}': 'invalid'}},
            {{'{JudgeDataKeys.NAME.value}': 'J3', '{JudgeDataKeys.SIDE.value}': 'neg'}}
        ]"""
        result = extract_ballots_from_judges(judges_str)
        # Should skip J2 with invalid side
        assert result == {"aff": 1, "neg": 1}

    def test_empty_judges_list(self):
        judges_str = "[]"
        result = extract_ballots_from_judges(judges_str)
        assert result == {"aff": 0, "neg": 0}

    def test_malformed_json_returns_none(self):
        judges_str = "[{invalid}]"
        result = extract_ballots_from_judges(judges_str)
        assert result is None

    def test_case_insensitive_side_uppercase(self):
        judges_str = f"""[
            {{'{JudgeDataKeys.NAME.value}': 'J1', '{JudgeDataKeys.SIDE.value}': 'AFF'}},
            {{'{JudgeDataKeys.NAME.value}': 'J2', '{JudgeDataKeys.SIDE.value}': 'NEG'}}
        ]"""
        result = extract_ballots_from_judges(judges_str)
        assert result == {"aff": 1, "neg": 1}

    def test_case_insensitive_side_mixed(self):
        judges_str = f"""[
            {{'{JudgeDataKeys.NAME.value}': 'J1', '{JudgeDataKeys.SIDE.value}': 'AfF'}},
            {{'{JudgeDataKeys.NAME.value}': 'J2', '{JudgeDataKeys.SIDE.value}': 'NeG'}}
        ]"""
        result = extract_ballots_from_judges(judges_str)
        assert result == {"aff": 1, "neg": 1}

    def test_single_judge_missing_score_returns_none(self):
        judges_str = f"""[
            {{
                '{JudgeDataKeys.NAME.value}': 'Judge One',
                '{JudgeDataKeys.SIDE.value}': 'aff'
            }}
        ]"""
        result = extract_ballots_from_judges(judges_str)
        assert result is None

    def test_single_judge_invalid_score_format_returns_none(self):
        judges_str = f"""[
            {{
                '{JudgeDataKeys.NAME.value}': 'Judge One',
                '{JudgeDataKeys.SIDE.value}': 'aff',
                '{JudgeDataKeys.SCORE.value}': 'invalid'
            }}
        ]"""
        result = extract_ballots_from_judges(judges_str)
        assert result is None


class TestFixSideSwapIfNeeded:
    def test_aff_wins_no_swap(self):
        """When aff wins, speakers should remain as-is."""
        aff_team = DebateTeam(
            team_name="Team A",
            side=Side.AFF,
            speakers=[
                ParsedSpeaker(name="Alice", points=75.0, position=1),
                ParsedSpeaker(name="Bob", points=76.0, position=2),
            ],
        )
        neg_team = DebateTeam(
            team_name="Team B",
            side=Side.NEG,
            speakers=[
                ParsedSpeaker(name="Dave", points=78.0, position=1),
                ParsedSpeaker(name="Eve", points=79.0, position=2),
            ],
        )

        corrected_aff, corrected_neg = fix_side_swap_if_needed(
            aff_team, neg_team, ballots_aff=2, ballots_neg=1, debate_id=1
        )

        # No swap should occur
        assert corrected_aff.team_name == "Team A"
        assert corrected_neg.team_name == "Team B"
        assert corrected_aff.speakers[0].name == "Alice"
        assert corrected_aff.speakers[1].name == "Bob"
        assert corrected_neg.speakers[0].name == "Dave"
        assert corrected_neg.speakers[1].name == "Eve"

    def test_neg_wins_swap_occurs(self):
        """When neg wins, speakers should be swapped between teams."""
        aff_team = DebateTeam(
            team_name="Team A",
            side=Side.AFF,
            speakers=[
                ParsedSpeaker(name="Alice", points=75.0, position=1),
                ParsedSpeaker(name="Bob", points=76.0, position=2),
            ],
        )
        neg_team = DebateTeam(
            team_name="Team B",
            side=Side.NEG,
            speakers=[
                ParsedSpeaker(name="Dave", points=78.0, position=1),
                ParsedSpeaker(name="Eve", points=79.0, position=2),
            ],
        )

        corrected_aff, corrected_neg = fix_side_swap_if_needed(
            aff_team, neg_team, ballots_aff=1, ballots_neg=2, debate_id=1
        )

        # Speakers should be swapped, but team names stay with their sides
        assert corrected_aff.team_name == "Team A"
        assert corrected_neg.team_name == "Team B"
        assert corrected_aff.speakers[0].name == "Dave"  # neg's speakers moved to aff
        assert corrected_aff.speakers[1].name == "Eve"
        assert corrected_neg.speakers[0].name == "Alice"  # aff's speakers moved to neg
        assert corrected_neg.speakers[1].name == "Bob"

    def test_tie_no_swap(self):
        """When it's a tie, speakers should remain as-is."""
        aff_team = DebateTeam(
            team_name="Team A",
            side=Side.AFF,
            speakers=[ParsedSpeaker(name="Alice", points=75.0, position=1)],
        )
        neg_team = DebateTeam(
            team_name="Team B",
            side=Side.NEG,
            speakers=[ParsedSpeaker(name="Dave", points=78.0, position=1)],
        )

        corrected_aff, corrected_neg = fix_side_swap_if_needed(
            aff_team, neg_team, ballots_aff=1, ballots_neg=1, debate_id=1
        )

        # No swap should occur
        assert corrected_aff.speakers[0].name == "Alice"
        assert corrected_neg.speakers[0].name == "Dave"

    def test_neg_wins_3_0_swap_occurs(self):
        """When neg wins unanimously, speakers should be swapped."""
        aff_team = DebateTeam(
            team_name="Team A",
            side=Side.AFF,
            speakers=[
                ParsedSpeaker(name="Alice", points=75.0, position=1),
                ParsedSpeaker(name="Bob", points=76.0, position=2),
                ParsedSpeaker(name="Charlie", points=77.0, position=3),
            ],
        )
        neg_team = DebateTeam(
            team_name="Team B",
            side=Side.NEG,
            speakers=[
                ParsedSpeaker(name="Dave", points=78.0, position=1),
                ParsedSpeaker(name="Eve", points=79.0, position=2),
                ParsedSpeaker(name="Frank", points=80.0, position=3),
            ],
        )

        corrected_aff, corrected_neg = fix_side_swap_if_needed(
            aff_team, neg_team, ballots_aff=0, ballots_neg=3, debate_id=1
        )

        # All speakers should be swapped
        assert corrected_aff.speakers[0].name == "Dave"
        assert corrected_aff.speakers[1].name == "Eve"
        assert corrected_aff.speakers[2].name == "Frank"
        assert corrected_neg.speakers[0].name == "Alice"
        assert corrected_neg.speakers[1].name == "Bob"
        assert corrected_neg.speakers[2].name == "Charlie"


class TestParseDebateRow:
    def test_valid_complete_debate_row(self):
        teams_json = f"""[
            {{
                "{TeamDataKeys.TEAM_NAME.value}": "Team A",
                "{TeamDataKeys.SIDE.value}": "aff",
                "{TeamDataKeys.SPEAKERS.value}": [
                    {{"{SpeakerDataKeys.NAME.value}": "Alice", "{SpeakerDataKeys.POINTS.value}": 75}},
                    {{"{SpeakerDataKeys.NAME.value}": "Bob", "{SpeakerDataKeys.POINTS.value}": 76}},
                    {{"{SpeakerDataKeys.NAME.value}": "Charlie", "{SpeakerDataKeys.POINTS.value}": 77}}
                ]
            }},
            {{
                "{TeamDataKeys.TEAM_NAME.value}": "Team B",
                "{TeamDataKeys.SIDE.value}": "neg",
                "{TeamDataKeys.SPEAKERS.value}": [
                    {{"{SpeakerDataKeys.NAME.value}": "Dave", "{SpeakerDataKeys.POINTS.value}": 78}},
                    {{"{SpeakerDataKeys.NAME.value}": "Eve", "{SpeakerDataKeys.POINTS.value}": 79}},
                    {{"{SpeakerDataKeys.NAME.value}": "Frank", "{SpeakerDataKeys.POINTS.value}": 80}}
                ]
            }}
        ]"""

        judges_json = f"""[
            {{
                "{JudgeDataKeys.NAME.value}": "Judge",
                "{JudgeDataKeys.SIDE.value}": "aff",
                "{JudgeDataKeys.SCORE.value}": "1:0"
            }}
        ]"""

        row = pd.Series(
            {
                InputCsvColumns.ID.value: 10700,
                InputCsvColumns.DATE.value: "2025-01-26 09:31:00",
                InputCsvColumns.TOURNAMENT_ID.value: 307,
                InputCsvColumns.TOURNAMENT_NAME.value: "Second Tournament",
                InputCsvColumns.MOTION.value: "Test motion",
                InputCsvColumns.TEAMS.value: teams_json,
                InputCsvColumns.JUDGES_SCORING.value: judges_json,
            }
        )

        result = parse_debate_row(row)

        assert result is not None
        assert result.debate_id == 10700
        assert result.tournament_id == 307
        assert result.tournament_name == "Second Tournament"
        assert result.motion == "Test motion"
        assert result.aff_team.team_name == "Team A"
        assert result.neg_team.team_name == "Team B"
        assert len(result.aff_team.speakers) == 3
        assert len(result.neg_team.speakers) == 3
        assert result.ballots_aff == 1
        assert result.ballots_neg == 0

    def test_debate_with_fewer_than_three_speakers_neg_wins(self):
        """Test that when neg wins with fewer speakers, the swap is applied."""
        teams_json = f"""[
            {{
                "{TeamDataKeys.TEAM_NAME.value}": "Team A",
                "{TeamDataKeys.SIDE.value}": "aff",
                "{TeamDataKeys.SPEAKERS.value}": [
                    {{"{SpeakerDataKeys.NAME.value}": "Alice", "{SpeakerDataKeys.POINTS.value}": 75}},
                    {{"{SpeakerDataKeys.NAME.value}": "Bob", "{SpeakerDataKeys.POINTS.value}": 76}}
                ]
            }},
            {{
                "{TeamDataKeys.TEAM_NAME.value}": "Team B",
                "{TeamDataKeys.SIDE.value}": "neg",
                "{TeamDataKeys.SPEAKERS.value}": [
                    {{"{SpeakerDataKeys.NAME.value}": "Dave", "{SpeakerDataKeys.POINTS.value}": 78}}
                ]
            }}
        ]"""

        judges_json = f"""[
            {{
                "{JudgeDataKeys.NAME.value}": "Judge",
                "{JudgeDataKeys.SIDE.value}": "neg",
                "{JudgeDataKeys.SCORE.value}": "1:0"
            }}
        ]"""

        row = pd.Series(
            {
                InputCsvColumns.ID.value: 10701,
                InputCsvColumns.DATE.value: "2025-01-26 09:31:00",
                InputCsvColumns.TOURNAMENT_ID.value: 307,
                InputCsvColumns.TOURNAMENT_NAME.value: "Second Tournament",
                InputCsvColumns.MOTION.value: "Test motion",
                InputCsvColumns.TEAMS.value: teams_json,
                InputCsvColumns.JUDGES_SCORING.value: judges_json,
            }
        )

        result = parse_debate_row(row)

        assert result is not None
        # After swap correction: Team A (aff) should have Dave (originally neg's speaker)
        # Team B (neg) should have Alice and Bob (originally aff's speakers)
        assert len(result.aff_team.speakers) == 1
        assert len(result.neg_team.speakers) == 2
        assert result.aff_team.speakers[0].name == "Dave"
        assert result.neg_team.speakers[0].name == "Alice"
        assert result.neg_team.speakers[1].name == "Bob"
        assert result.ballots_aff == 0
        assert result.ballots_neg == 1

    def test_missing_aff_team(self):
        teams_json = f"""[
            {{
                "{TeamDataKeys.TEAM_NAME.value}": "Team B",
                "{TeamDataKeys.SIDE.value}": "neg",
                "{TeamDataKeys.SPEAKERS.value}": [
                    {{"{SpeakerDataKeys.NAME.value}": "Dave", "{SpeakerDataKeys.POINTS.value}": 78}}
                ]
            }}
        ]"""

        judges_json = f"""[
            {{
                "{JudgeDataKeys.NAME.value}": "Judge",
                "{JudgeDataKeys.SIDE.value}": "neg",
                "{JudgeDataKeys.SCORE.value}": "1:0"
            }}
        ]"""

        row = pd.Series(
            {
                InputCsvColumns.ID.value: 10702,
                InputCsvColumns.DATE.value: "2025-01-26 09:31:00",
                InputCsvColumns.TOURNAMENT_ID.value: 307,
                InputCsvColumns.TOURNAMENT_NAME.value: "Second Tournament",
                InputCsvColumns.MOTION.value: "Test motion",
                InputCsvColumns.TEAMS.value: teams_json,
                InputCsvColumns.JUDGES_SCORING.value: judges_json,
            }
        )

        result = parse_debate_row(row)
        assert result is None

    def test_missing_neg_team(self):
        teams_json = f"""[
            {{
                "{TeamDataKeys.TEAM_NAME.value}": "Team A",
                "{TeamDataKeys.SIDE.value}": "aff",
                "{TeamDataKeys.SPEAKERS.value}": [
                    {{"{SpeakerDataKeys.NAME.value}": "Alice", "{SpeakerDataKeys.POINTS.value}": 75}}
                ]
            }}
        ]"""

        judges_json = f"""[
            {{
                "{JudgeDataKeys.NAME.value}": "Judge",
                "{JudgeDataKeys.SIDE.value}": "aff",
                "{JudgeDataKeys.SCORE.value}": "1:0"
            }}
        ]"""

        row = pd.Series(
            {
                InputCsvColumns.ID.value: 10703,
                InputCsvColumns.DATE.value: "2025-01-26 09:31:00",
                InputCsvColumns.TOURNAMENT_ID.value: 307,
                InputCsvColumns.TOURNAMENT_NAME.value: "Second Tournament",
                InputCsvColumns.MOTION.value: "Test motion",
                InputCsvColumns.TEAMS.value: teams_json,
                InputCsvColumns.JUDGES_SCORING.value: judges_json,
            }
        )

        result = parse_debate_row(row)
        assert result is None

    def test_invalid_team_count_more_than_two(self):
        teams_json = f"""[
            {{"{TeamDataKeys.TEAM_NAME.value}": "Team A", "{TeamDataKeys.SIDE.value}": "aff", "{TeamDataKeys.SPEAKERS.value}": []}},
            {{"{TeamDataKeys.TEAM_NAME.value}": "Team B", "{TeamDataKeys.SIDE.value}": "neg", "{TeamDataKeys.SPEAKERS.value}": []}},
            {{"{TeamDataKeys.TEAM_NAME.value}": "Team C", "{TeamDataKeys.SIDE.value}": "aff", "{TeamDataKeys.SPEAKERS.value}": []}}
        ]"""

        judges_json = f"""[
            {{
                "{JudgeDataKeys.NAME.value}": "Judge",
                "{JudgeDataKeys.SIDE.value}": "aff",
                "{JudgeDataKeys.SCORE.value}": "1:0"
            }}
        ]"""

        row = pd.Series(
            {
                InputCsvColumns.ID.value: 10704,
                InputCsvColumns.DATE.value: "2025-01-26 09:31:00",
                InputCsvColumns.TOURNAMENT_ID.value: 307,
                InputCsvColumns.TOURNAMENT_NAME.value: "Second Tournament",
                InputCsvColumns.MOTION.value: "Test motion",
                InputCsvColumns.TEAMS.value: teams_json,
                InputCsvColumns.JUDGES_SCORING.value: judges_json,
            }
        )

        result = parse_debate_row(row)
        assert result is None

    def test_invalid_side_value(self):
        teams_json = f"""[
            {{
                "{TeamDataKeys.TEAM_NAME.value}": "Team A",
                "{TeamDataKeys.SIDE.value}": "invalid",
                "{TeamDataKeys.SPEAKERS.value}": [
                    {{"{SpeakerDataKeys.NAME.value}": "Alice", "{SpeakerDataKeys.POINTS.value}": 75}}
                ]
            }},
            {{
                "{TeamDataKeys.TEAM_NAME.value}": "Team B",
                "{TeamDataKeys.SIDE.value}": "neg",
                "{TeamDataKeys.SPEAKERS.value}": [
                    {{"{SpeakerDataKeys.NAME.value}": "Dave", "{SpeakerDataKeys.POINTS.value}": 78}}
                ]
            }}
        ]"""

        judges_json = f"""[
            {{
                "{JudgeDataKeys.NAME.value}": "Judge",
                "{JudgeDataKeys.SIDE.value}": "neg",
                "{JudgeDataKeys.SCORE.value}": "1:0"
            }}
        ]"""

        row = pd.Series(
            {
                InputCsvColumns.ID.value: 10705,
                InputCsvColumns.DATE.value: "2025-01-26 09:31:00",
                InputCsvColumns.TOURNAMENT_ID.value: 307,
                InputCsvColumns.TOURNAMENT_NAME.value: "Second Tournament",
                InputCsvColumns.MOTION.value: "Test motion",
                InputCsvColumns.TEAMS.value: teams_json,
                InputCsvColumns.JUDGES_SCORING.value: judges_json,
            }
        )

        result = parse_debate_row(row)
        assert result is None

    def test_malformed_teams_json(self):
        row = pd.Series(
            {
                InputCsvColumns.ID.value: 10706,
                InputCsvColumns.DATE.value: "2025-01-26 09:31:00",
                InputCsvColumns.TOURNAMENT_ID.value: 307,
                InputCsvColumns.TOURNAMENT_NAME.value: "Second Tournament",
                InputCsvColumns.MOTION.value: "Test motion",
                InputCsvColumns.TEAMS.value: "[{invalid json}]",
                InputCsvColumns.JUDGES_SCORING.value: f"""[
                    {{
                        "{JudgeDataKeys.NAME.value}": "Judge",
                        "{JudgeDataKeys.SIDE.value}": "aff",
                        "{JudgeDataKeys.SCORE.value}": "1:0"
                    }}
                ]""",
            }
        )

        result = parse_debate_row(row)
        assert result is None

    def test_malformed_judges_json(self):
        teams_json = f"""[
            {{
                "{TeamDataKeys.TEAM_NAME.value}": "Team A",
                "{TeamDataKeys.SIDE.value}": "aff",
                "{TeamDataKeys.SPEAKERS.value}": [
                    {{"{SpeakerDataKeys.NAME.value}": "Alice", "{SpeakerDataKeys.POINTS.value}": 75}}
                ]
            }},
            {{
                "{TeamDataKeys.TEAM_NAME.value}": "Team B",
                "{TeamDataKeys.SIDE.value}": "neg",
                "{TeamDataKeys.SPEAKERS.value}": [
                    {{"{SpeakerDataKeys.NAME.value}": "Dave", "{SpeakerDataKeys.POINTS.value}": 78}}
                ]
            }}
        ]"""

        row = pd.Series(
            {
                InputCsvColumns.ID.value: 10707,
                InputCsvColumns.DATE.value: "2025-01-26 09:31:00",
                InputCsvColumns.TOURNAMENT_ID.value: 307,
                InputCsvColumns.TOURNAMENT_NAME.value: "Second Tournament",
                InputCsvColumns.MOTION.value: "Test motion",
                InputCsvColumns.TEAMS.value: teams_json,
                InputCsvColumns.JUDGES_SCORING.value: "[{invalid}]",
            }
        )

        result = parse_debate_row(row)
        assert result is None

    def test_speaker_positions_assigned_correctly(self):
        teams_json = f"""[
            {{
                "{TeamDataKeys.TEAM_NAME.value}": "Team A",
                "{TeamDataKeys.SIDE.value}": "aff",
                "{TeamDataKeys.SPEAKERS.value}": [
                    {{"{SpeakerDataKeys.NAME.value}": "Alice", "{SpeakerDataKeys.POINTS.value}": 75}},
                    {{"{SpeakerDataKeys.NAME.value}": "Bob", "{SpeakerDataKeys.POINTS.value}": 76}},
                    {{"{SpeakerDataKeys.NAME.value}": "Charlie", "{SpeakerDataKeys.POINTS.value}": 77}}
                ]
            }},
            {{
                "{TeamDataKeys.TEAM_NAME.value}": "Team B",
                "{TeamDataKeys.SIDE.value}": "neg",
                "{TeamDataKeys.SPEAKERS.value}": [
                    {{"{SpeakerDataKeys.NAME.value}": "Dave", "{SpeakerDataKeys.POINTS.value}": 78}},
                    {{"{SpeakerDataKeys.NAME.value}": "Eve", "{SpeakerDataKeys.POINTS.value}": 79}},
                    {{"{SpeakerDataKeys.NAME.value}": "Frank", "{SpeakerDataKeys.POINTS.value}": 80}}
                ]
            }}
        ]"""

        judges_json = f"""[
            {{
                "{JudgeDataKeys.NAME.value}": "Judge",
                "{JudgeDataKeys.SIDE.value}": "aff",
                "{JudgeDataKeys.SCORE.value}": "1:0"
            }}
        ]"""

        row = pd.Series(
            {
                InputCsvColumns.ID.value: 10708,
                InputCsvColumns.DATE.value: "2025-01-26 09:31:00",
                InputCsvColumns.TOURNAMENT_ID.value: 307,
                InputCsvColumns.TOURNAMENT_NAME.value: "Second Tournament",
                InputCsvColumns.MOTION.value: "Test motion",
                InputCsvColumns.TEAMS.value: teams_json,
                InputCsvColumns.JUDGES_SCORING.value: judges_json,
            }
        )

        result = parse_debate_row(row)

        assert result is not None
        assert result.aff_team.speakers[0].position == 1
        assert result.aff_team.speakers[1].position == 2
        assert result.aff_team.speakers[2].position == 3
        assert result.neg_team.speakers[0].position == 1
        assert result.neg_team.speakers[1].position == 2
        assert result.neg_team.speakers[2].position == 3


class TestDebateToSpeeches:
    def test_standard_debate_three_speakers_per_side(self):
        parsed_debate = ParsedDebate(
            debate_id=1,
            date=datetime(2025, 1, 26),
            tournament_id=307,
            tournament_name="Test Tournament",
            motion="Test motion",
            aff_team=DebateTeam(
                team_name="Team A",
                side=Side.AFF,
                speakers=[
                    ParsedSpeaker(name="Alice", points=75.0, position=1),
                    ParsedSpeaker(name="Bob", points=76.0, position=2),
                    ParsedSpeaker(name="Charlie", points=77.0, position=3),
                ],
            ),
            neg_team=DebateTeam(
                team_name="Team B",
                side=Side.NEG,
                speakers=[
                    ParsedSpeaker(name="Dave", points=78.0, position=1),
                    ParsedSpeaker(name="Eve", points=79.0, position=2),
                    ParsedSpeaker(name="Frank", points=80.0, position=3),
                ],
            ),
            ballots_aff=2,
            ballots_neg=1,
        )

        speeches = debate_to_speeches(parsed_debate)

        assert len(speeches) == 6
        # Check aff speeches
        assert speeches[0].side == Side.AFF
        assert speeches[0].speaker_name == "Alice"
        assert speeches[0].ballots_gained == 2
        assert speeches[0].opponent_team_name == "Team B"
        assert speeches[1].speaker_name == "Bob"
        assert speeches[2].speaker_name == "Charlie"
        # Check neg speeches
        assert speeches[3].side == Side.NEG
        assert speeches[3].speaker_name == "Dave"
        assert speeches[3].ballots_gained == 1
        assert speeches[3].opponent_team_name == "Team A"
        assert speeches[4].speaker_name == "Eve"
        assert speeches[5].speaker_name == "Frank"

    def test_debate_with_two_speakers_per_side(self):
        parsed_debate = ParsedDebate(
            debate_id=2,
            date=datetime(2025, 1, 26),
            tournament_id=307,
            tournament_name="Test Tournament",
            motion="Test motion",
            aff_team=DebateTeam(
                team_name="Team A",
                side=Side.AFF,
                speakers=[
                    ParsedSpeaker(name="Alice", points=75.0, position=1),
                    ParsedSpeaker(name="Bob", points=76.0, position=2),
                ],
            ),
            neg_team=DebateTeam(
                team_name="Team B",
                side=Side.NEG,
                speakers=[
                    ParsedSpeaker(name="Dave", points=78.0, position=1),
                    ParsedSpeaker(name="Eve", points=79.0, position=2),
                ],
            ),
            ballots_aff=0,
            ballots_neg=3,
        )

        speeches = debate_to_speeches(parsed_debate)

        assert len(speeches) == 4

    def test_debate_with_one_speaker_per_side(self):
        parsed_debate = ParsedDebate(
            debate_id=3,
            date=datetime(2025, 1, 26),
            tournament_id=307,
            tournament_name="Test Tournament",
            motion="Test motion",
            aff_team=DebateTeam(
                team_name="Team A",
                side=Side.AFF,
                speakers=[ParsedSpeaker(name="Alice", points=75.0, position=1)],
            ),
            neg_team=DebateTeam(
                team_name="Team B",
                side=Side.NEG,
                speakers=[ParsedSpeaker(name="Dave", points=78.0, position=1)],
            ),
            ballots_aff=1,
            ballots_neg=0,
        )

        speeches = debate_to_speeches(parsed_debate)

        assert len(speeches) == 2

    def test_ballots_gained_matches_team_ballot_count(self):
        parsed_debate = ParsedDebate(
            debate_id=4,
            date=datetime(2025, 1, 26),
            tournament_id=307,
            tournament_name="Test Tournament",
            motion="Test motion",
            aff_team=DebateTeam(
                team_name="Team A",
                side=Side.AFF,
                speakers=[ParsedSpeaker(name="Alice", points=75.0, position=1)],
            ),
            neg_team=DebateTeam(
                team_name="Team B",
                side=Side.NEG,
                speakers=[ParsedSpeaker(name="Dave", points=78.0, position=1)],
            ),
            ballots_aff=2,
            ballots_neg=1,
        )

        speeches = debate_to_speeches(parsed_debate)

        aff_speech = speeches[0]
        neg_speech = speeches[1]

        assert aff_speech.ballots_gained == 2
        assert neg_speech.ballots_gained == 1

    def test_opponent_team_name_correct_for_each_side(self):
        parsed_debate = ParsedDebate(
            debate_id=5,
            date=datetime(2025, 1, 26),
            tournament_id=307,
            tournament_name="Test Tournament",
            motion="Test motion",
            aff_team=DebateTeam(
                team_name="Affirmative Team",
                side=Side.AFF,
                speakers=[ParsedSpeaker(name="Alice", points=75.0, position=1)],
            ),
            neg_team=DebateTeam(
                team_name="Negative Team",
                side=Side.NEG,
                speakers=[ParsedSpeaker(name="Dave", points=78.0, position=1)],
            ),
            ballots_aff=3,
            ballots_neg=0,
        )

        speeches = debate_to_speeches(parsed_debate)

        aff_speech = speeches[0]
        neg_speech = speeches[1]

        assert aff_speech.opponent_team_name == "Negative Team"
        assert neg_speech.opponent_team_name == "Affirmative Team"

    def test_speaker_positions_correctly_assigned(self):
        parsed_debate = ParsedDebate(
            debate_id=6,
            date=datetime(2025, 1, 26),
            tournament_id=307,
            tournament_name="Test Tournament",
            motion="Test motion",
            aff_team=DebateTeam(
                team_name="Team A",
                side=Side.AFF,
                speakers=[
                    ParsedSpeaker(name="Alice", points=75.0, position=1),
                    ParsedSpeaker(name="Bob", points=76.0, position=2),
                    ParsedSpeaker(name="Charlie", points=77.0, position=3),
                ],
            ),
            neg_team=DebateTeam(
                team_name="Team B",
                side=Side.NEG,
                speakers=[
                    ParsedSpeaker(name="Dave", points=78.0, position=1),
                    ParsedSpeaker(name="Eve", points=79.0, position=2),
                    ParsedSpeaker(name="Frank", points=80.0, position=3),
                ],
            ),
            ballots_aff=1,
            ballots_neg=2,
        )

        speeches = debate_to_speeches(parsed_debate)

        assert speeches[0].speaker_position == 1
        assert speeches[1].speaker_position == 2
        assert speeches[2].speaker_position == 3
        assert speeches[3].speaker_position == 1
        assert speeches[4].speaker_position == 2
        assert speeches[5].speaker_position == 3

    def test_all_metadata_carried_over(self):
        test_date = datetime(2025, 1, 26, 9, 31, 0)
        parsed_debate = ParsedDebate(
            debate_id=123,
            date=test_date,
            tournament_id=999,
            tournament_name="Championship Tournament",
            motion="This house believes in testing",
            aff_team=DebateTeam(
                team_name="Team A",
                side=Side.AFF,
                speakers=[ParsedSpeaker(name="Alice", points=75.0, position=1)],
            ),
            neg_team=DebateTeam(
                team_name="Team B",
                side=Side.NEG,
                speakers=[ParsedSpeaker(name="Dave", points=78.0, position=1)],
            ),
            ballots_aff=2,
            ballots_neg=1,
        )

        speeches = debate_to_speeches(parsed_debate)

        for speech in speeches:
            assert speech.debate_id == 123
            assert speech.date == test_date
            assert speech.tournament_id == 999
            assert speech.tournament_name == "Championship Tournament"
            assert speech.motion == "This house believes in testing"
