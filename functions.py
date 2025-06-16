import pandas as pd
import re
from difflib import SequenceMatcher


def interpret_workout(workout_string, alias_data):
    """
    Process a workout string into structured data including matched exercises and extracted details.
    """
    if not workout_string:
        return {'error': 'No workout string provided'}

    try:
        # Parse and match the workout string
        parsed_data = process_prompt_with_top_matches(workout_string, alias_data)

    except Exception as e:
        # Log full traceback for debugging
        import traceback
        print("ERROR in process_prompt_with_top_matches:\n", traceback.format_exc())
        return {'error': 'Internal processing error'}

    return {'workout_data': parsed_data}

def process_prompt_with_top_matches(prompt, alias_data):
    """
    Process a workout prompt, parse the exercises, match them to known aliases,
    and extract details like sets, reps, and weight.
    """

    # Parse the prompt into structured exercise data with top matches
    parsed = parse_exercises(prompt, [e['name'] for e in alias_data], alias_data)
    output = {}

    for raw_name, match_data in parsed.items():
        # Find the original line that corresponds to the raw_name for detail extraction
        pattern = re.compile(re.escape(raw_name), re.IGNORECASE)
        line = next((l for l in prompt.split("\n") if pattern.search(l)), "")

        # Extract sets, reps, weight, etc.
        details = extract_details(line)

        matched_list = match_data['top_matches']
        # Get the ID of the best match if available
        first_id = matched_list[0]['id'] if matched_list else None

        # Build output for this exercise
        output[raw_name] = {
            'id': first_id,                          # ID of the best matched exercise
            'raw_name': raw_name,                    # The raw name as parsed from the prompt
            'top_matches': match_data['top_matches'],# List of top 3 matches (if found)
            'set_structure': match_data['set_structure'],  # 0 = regular, 1 = superset, 2 = circuit
            'group_id': match_data.get('group_id'),  # Group ID for superset/circuit
            'details': matched_list and details or None   # Extracted details if matched
        }

    return output

def parse_exercises(prompts, exercise_library, df_aliases):
    """
    Parse a workout text prompt into structured exercise data,
    detecting set structures (e.g., superset, circuit) and grouping.
    """

    # Split prompt into individual lines and initialize state
    lines = prompts.strip().split("\n")
    exercises = []

    current_structure = 0  # 0 = none, 1 = superset, 2 = circuit
    group_id_counter = 1
    current_group_id = 1
    prev_structure = None

    # Process each line
    for i, line in enumerate(lines):
        line = line.strip().lower()

        # Detect set structure headers
        if line.startswith("superset"):
            current_structure = 1
            current_group_id = group_id_counter
            group_id_counter += 1
            continue
        elif line.startswith("circuit"):
            current_structure = 2
            current_group_id = group_id_counter
            group_id_counter += 1
            continue
        elif not line:
            # Reset structure on empty line
            current_structure = 0
            prev_structure = None
            continue
        elif re.match(r"^(repeat|rest)$", line) or line.startswith("hiit"):
            # Skip non-exercise lines
            continue

        # Handle transition between structures
        if prev_structure is not None and prev_structure != current_structure:
            if current_structure != 0:
                current_group_id = group_id_counter
                group_id_counter += 1

        # Extract potential exercise name
        match = re.match(r"([A-Za-z\s\-]+)", line)
        if match:
            exercise_name = match.group(1).strip()

            # Assign group if no current structure
            if current_structure == 0:
                current_group_id = group_id_counter
                group_id_counter += 1

            # Save the exercise info
            exercises.append({
                'name': exercise_name,
                'set_structure': current_structure,
                'group_id': current_group_id
            })

        prev_structure = current_structure

    # Build final result with matched exercise data
    final_dict = {}
    for ex in exercises:
        matched_exercises = match_exercise(ex['name'], df_aliases)
        final_dict[ex['name']] = {
            "top_matches": matched_exercises,
            "set_structure": ex['set_structure'],
            "group_id": ex['group_id']
        }

    return final_dict

def extract_details(exercise_str):
    """
    Extract sets, reps, weight, RIR/RPE, and rest details from an exercise string.
    """
    exercise_str = fallback_handling(exercise_str)

    details = {
        'sets': None,
        'reps': None,
        'weight': None,
        'rir': None,
        'rir_or_rpe': 0,   # 0 = RIR, 1 = RPE
        'rest': None,
        'weight_unit': 0   # 0 = lbs, 1 = kg
    }

    # Match sets (e.g. 3x, 4-)
    match_sets = re.search(r"(\d+)\s*[x\-]", exercise_str)
    if match_sets:
        details['sets'] = int(match_sets.group(1))

    # Match reps (e.g. x10, -12, x10,12,Max)
    match_reps = re.search(r"[x\-]\s*([\d,Max\s]+)", exercise_str, re.IGNORECASE)
    if match_reps:
        rep_values = match_reps.group(1).replace(" ", "").split(',')
        details['reps'] = [int(rep) if rep.isdigit() else rep for rep in rep_values]

    # Match weight: @ or ( )
    match_weight_at = re.search(r"@(\d+)\s*(lbs|kg)?", exercise_str, re.IGNORECASE)
    match_weight_paren = re.search(r"\((\d+)\s*(lbs|kg)?\)", exercise_str, re.IGNORECASE)

    weight = None
    unit = 'lbs'

    if match_weight_at:
        weight = int(match_weight_at.group(1))
        unit = match_weight_at.group(2).lower() if match_weight_at.group(2) else 'lbs'
    elif match_weight_paren:
        weight = int(match_weight_paren.group(1))
        unit = match_weight_paren.group(2).lower() if match_weight_paren.group(2) else 'lbs'

    if weight is not None:
        details['weight'] = [weight]
        details['weight_unit'] = 1 if unit == 'kg' else 0

    # Match RIR or RPE (e.g. 2RIR, 8RPE)
    match_rir_rpe = re.search(r"(\d+)(rir|rpe)", exercise_str, re.IGNORECASE)
    if match_rir_rpe:
        details['rir'] = int(match_rir_rpe.group(1))
        details['rir_or_rpe'] = 0 if match_rir_rpe.group(2).lower() == 'rir' else 1

    # Match rest (e.g. 60s rest, 1min rest)
    match_rest = re.search(r"(\d+)\s*(s|min|seconds|minutes)\s*(rest)?", exercise_str, re.IGNORECASE)
    if match_rest:
        time_val = match_rest.group(1)
        time_unit = match_rest.group(2).lower()
        if time_unit in ['s', 'seconds']:
            details['rest'] = f"{time_val}s"
        else:
            details['rest'] = f"{time_val}min"

    return details


def normalize(text: str) -> str:
    """
    Normalize exercise name strings for consistent matching.
    - Converts the input text to lowercase.
    - Strips leading and trailing whitespace.
    """
    return text.lower().strip()


def match_exercise(exercise_name, alias_data):
    """
    Attempt to find the best matching exercise(s) for a given input name,
    searching first by primary exercise names, then by known aliases.
    """

    # Extract the primary exercise names for initial matching
    primary_names = [entry['name'] for entry in alias_data]

    # Create a mapping from normalized names and aliases to their canonical name and id
    all_aliases = {}
    for entry in alias_data:
        main_name = entry['name']
        entry_id = entry['id']

        # Map normalized main name to its canonical info
        all_aliases[normalize(main_name)] = {'name': main_name, 'id': entry_id}

        # Also map normalized aliases to the same canonical info
        for a in ('alias_1', 'alias_2'):
            if entry.get(a):
                all_aliases[normalize(entry[a])] = {'name': main_name, 'id': entry_id}

    # First attempt: try to match directly against primary names with a high similarity threshold
    top = match_exercise_top3(exercise_name, primary_names, initial_cutoff=0.95)
    if top:
        # Return the top matches with canonical ids and rounded scores
        return [
            {
                'name': name,
                'id': all_aliases[normalize(name)]['id'],
                'score': round(score, 2)
            }
            for name, score in top
        ]

    # Second attempt: try to match against all known aliases with a lower similarity threshold
    alias_keys = list(all_aliases.keys())
    top_alias = match_exercise_top3(exercise_name, alias_keys, initial_cutoff=0.80)
    if top_alias:
        # Return the matches found via alias names with their canonical names and ids
        return [
            {
                'name': all_aliases[normalize(alias)]['name'],
                'id': all_aliases[normalize(alias)]['id'],
                'score': round(score, 2)
            }
            for alias, score in top_alias
        ]

    # If no matches found, return empty list
    return []

def match_exercise_top3(exercise_name, exercise_library, initial_cutoff=0.80, step=0.05, min_cutoff=0.5):
    """
    Find the top 3 best matching exercise names from a library based on string similarity.
    """
    norm_name = normalize(exercise_name)

    scored = []
    for original in exercise_library:
        norm_orig = normalize(original)
        score = SequenceMatcher(None, norm_name, norm_orig).ratio()
        scored.append((original, score))

    cutoff = initial_cutoff
    while cutoff >= min_cutoff:
        candidates = [pair for pair in scored if pair[1] >= cutoff]
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[:3]
        cutoff -= step

    return []

def fallback_handling(exercise_str):
    """
    Normalize exercise string formatting for easier parsing.
    Removes unnecessary spaces and standardizes common patterns.
    """

    # Convert entire string to lowercase for consistency
    exercise_str = exercise_str.lower()

    # Remove spaces around 'x' (e.g., "3 x 10" -> "3x10")
    exercise_str = re.sub(r"(\d)\s*x\s*(\d)", r"\1x\2", exercise_str)

    # Remove spaces between number and weight unit (e.g., "100 lbs" -> "100lbs")
    exercise_str = re.sub(r"(\d)\s*(lbs|kg)", r"\1\2", exercise_str)

    # Remove spaces after '@' in weight notations (e.g., "@ 100lbs" -> "@100lbs")
    exercise_str = re.sub(r"@\s*(\d+\s*(lbs|kg))", r"@\1", exercise_str)

    # Remove spaces inside parentheses around weight (e.g., "( 100 lbs )" -> "(100lbs)")
    exercise_str = re.sub(r"\(\s*(\d+\s*(lbs|kg))\s*\)", r"(\1)", exercise_str)

    # Remove spaces between number and 'rir' or 'rpe' (e.g., "2 rir" -> "2rir")
    exercise_str = re.sub(r"(\d+)\s*(rir|rpe)", r"\1\2", exercise_str)

    return exercise_str


def result_to_dataframe(result):
    data = []
    for exercise, info in result['workout_data'].items():
        row = {
            'exercise': exercise,
            'id': info.get('id'),
            'raw_name': info.get('raw_name'),
            'set_structure': info.get('set_structure'),
            'group_id': info.get('group_id'),
        }
        details = info.get('details') or {}
        
        # Add details fields, handle None safely
        row['sets'] = details.get('sets')
        row['reps'] = details.get('reps')
        row['weight'] = details.get('weight')
        row['rir'] = details.get('rir')
        row['rir_or_rpe'] = details.get('rir_or_rpe')
        row['rest'] = details.get('rest')
        row['weight_unit'] = details.get('weight_unit')

        # Optionally, include top_matches as a string or count
        row['top_matches'] = ', '.join([m['name'] for m in info.get('top_matches', [])])

        data.append(row)

    return pd.DataFrame(data)