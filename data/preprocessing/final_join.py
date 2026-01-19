"""
Join tidy debate data with debater genders and motion categories.
"""

import pandas as pd

from constants import (
    PATH_TO_CATEGORIZATION_OUTPUT,
    PATH_TO_DEBATER_AGES_FILE,
    PATH_TO_FINAL_OUTPUT,
    PATH_TO_GENDER_OUTPUT,
    PATH_TO_TIDY_OUTPUT,
)


def main():
    print("Loading data files...")
    tidy_data = pd.read_csv(PATH_TO_TIDY_OUTPUT)
    debater_genders = pd.read_csv(PATH_TO_GENDER_OUTPUT)
    motion_categories = pd.read_csv(PATH_TO_CATEGORIZATION_OUTPUT)
    debater_first_debate = pd.read_csv(PATH_TO_DEBATER_AGES_FILE)

    print("Joining debater genders...")
    merged_data = tidy_data.merge(
        debater_genders, left_on="speaker_name", right_on="debater_name", how="left"
    )

    merged_data = merged_data.drop(columns=["debater_name"])

    print("Joining motion categories...")
    final_data = merged_data.merge(motion_categories, on="motion", how="left")

    print("Joining debaters' time of first debate...")
    final_data = final_data.merge(
        debater_first_debate, left_on="speaker_name", right_on="name", how="left"
    )
    final_data = final_data.drop(columns=["name"])
    final_data = final_data.rename(
        columns={"date_x": "debate_date", "date_y": "speaker_first_debate_date"}
    )

    print(f"Final data shape: {final_data.shape}")
    print(f"Columns: {final_data.columns.tolist()}")

    return final_data


def save_final_data(final_data: pd.DataFrame):
    final_data.to_csv(PATH_TO_FINAL_OUTPUT, index=False)
    print(f"\nSaved to: {PATH_TO_FINAL_OUTPUT}")


if __name__ == "__main__":
    result = main()
    save_final_data(result)
