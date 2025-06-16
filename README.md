# Lightweight-WorkoutNLP

## Overview
This project contains a parsing and matching algorithm designed to process natural language workout prompts. It extracts structured exercise data—including exercise names, sets, reps, weights, and more—and matches them to a comprehensive exercise library using fuzzy matching techniques. This enables transforming loosely formatted workout text into clean, structured data suitable for fitness applications.

## Exercise Library
This project includes a comprehensive exercise library with approximately 1000 entries, featuring exercise names, common aliases, muscle groups, equipment, instructions, and descriptions. The library was manually curated and refined by me, leveraging my background with a Master’s degree in Exercise Physiology and extensive experience as a personal trainer. It is designed primarily at a beginner level and can be easily integrated with this algorithm or other external tools to support fitness applications, training programs, or educational resources.

Because of this careful curation and domain expertise, the library is highly accurate and can be utilized not only for this parsing and matching algorithm but also for other fitness-related projects, apps, or research that require a reliable exercise database.

If you plan to build fitness applications, training loggers, or AI assistants in the exercise domain, this library provides a strong foundational dataset to build upon.

## Features
- Parse workout prompts with supersets, circuits, and individual exercises
- Normalize and match exercise names using fuzzy matching
- Extract sets, reps, weights, RIR/RPE, rest times, and more
- Handle aliases and fallback name variations
- Return structured data with match confidence scores

## Setup
Clone the repo
Install dependencies - e.g., pip install pandas ()
Load your exercise library CSV file (e.g., ExerciseLibrary.csv)
Run example scripts or call interpret_workout() with your workout string


## File Structure
algorithmTraining.ipynb — Simple notebook to run and test example prompts through the parsing algorithm
functions.py — Core parsing, matching, and detail extraction functions
example_prompts.txt — Sample workout prompt inputs for testing and development
ExerciseLibrary.csv — Exercise library with names and aliases (~1000 entries) used for matching
AppImages/ — Folder containing images demonstrating how the algorithm integrates with the iOS app
README.md — This documentation file

## Notes
Matching thresholds and fallback handling can be tuned for your dataset
Designed to be extensible for new exercise types or detail extraction

## Contributing & Collaboration
This project is fully open source and free to use. I have an existing iOS app that integrates this algorithm, and I’m actively looking to improve and expand its capabilities.

If you'd like to contribute enhancements, report issues, or add new features, please feel free to submit a pull request.

If you’re interested in collaborating to help build or improve the app—whether through development, UI/UX, or other ideas—please reach out to me at ddiaz1126@yahoo.com. I’m excited to connect with developers and fitness enthusiasts to make this tool even better.

## License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

Feel free to use, modify, and distribute this software freely.
