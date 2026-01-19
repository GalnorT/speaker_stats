"""
Join tidy debate data with debater genders and motion categories.
"""

import pandas as pd

from constants import (
    PATH_TO_CATEGORIZATION_OUTPUT,
    PATH_TO_FINAL_OUTPUT,
    PATH_TO_GENDER_OUTPUT,
    PATH_TO_TIDY_OUTPUT,
)


def main():
    print("Loading data files...")
    tidy_data = pd.read_csv(PATH_TO_TIDY_OUTPUT)
    debater_genders = pd.read_csv(PATH_TO_GENDER_OUTPUT)
    motion_categories = pd.read_csv(PATH_TO_CATEGORIZATION_OUTPUT)

    print("Joining debater genders...")
    merged_data = tidy_data.merge(
        debater_genders, left_on="speaker_name", right_on="debater_name", how="left"
    )

    merged_data = merged_data.drop(columns=["debater_name"])

    print("Joining motion categories...")
    final_data = merged_data.merge(motion_categories, on="motion", how="left")

    print(f"Final data shape: {final_data.shape}")
    print(f"Columns: {final_data.columns.tolist()}")

    return final_data


def save_final_data(final_data: pd.DataFrame):
    final_data.to_csv(PATH_TO_FINAL_OUTPUT, index=False)
    print(f"\nSaved to: {PATH_TO_FINAL_OUTPUT}")


if __name__ == "__main__":
    result = main()
    save_final_data(result)
