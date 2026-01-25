# IES Python Course - Project Review Guide

Thank you for taking the time to review this project! This document is designed to help you navigate the repository and hopefully save you time grading.

## Submission State

Since we have gotten some real users to use and give feedback on the dashboard, we will likely make more commits even after the submission deadline.

To review the exact state submitted for grading, please check out the release tag:

```bash
git checkout IES-Python-submission
```

Alternatively, you can view the release on GitHub at the "Releases" section of the repository.

## Repository Structure

Here's an overview of the main folders in this project:

- **`analysis/`** - Contains the final Jupyter notebook with the results of our data analysis
- **`data/`** - Contains both raw and preprocessed data, along with several data processing scripts
- **`docs/`** - GitHub Pages deployment folder - serves the static website for our visualization dashboard
- **`logger/`** - A simple logging utility used throughout the project. Outputs logs to both stdout and `.logger/logs/log.jsonl`
- **`scraping/`** - Scripts we used to scrape the original dataset
- **`tests/`** - Contains 96 unit tests covering the preprocessing scripts
- **`web/`** - TypeScript source code for the dashboard/visualization app deployed to GitHub Pages

## What's Runnable

All preprocessing scripts are fully functional and can be run with the `--help` flag to see usage instructions:

```bash
python -m data.preprocessing.estimate_gender --help
```

We **do not recommend** running the scraping scripts, as they hit live servers that are sometimes down for maintenance. We cannot guarantee they will work during review.

The visualization dashboard is deployed and accessible at:
**https://galnort.github.io/speaker_stats/**

## Troubleshooting Tips

If you encounter any issues while running the code:

1. Run the tests first - We have 96 unit tests that should help diagnose issues:

   ```bash
   pytest
   ```

2. Check the logs - If tests pass but something still isn't working, the `.logger/logs/log.jsonl` file may contain useful debugging information

---

Thank you again for your time and for teaching such a wonderful course! We hope you find our project interesting and well-structured.
