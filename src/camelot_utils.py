# camelot_converter.py

# Comprehensive mapping of musical keys to Camelot codes.
# Keys are generally lowercase and include common variations and abbreviations
# to make the lookup more robust.
CAMELOT_KEY_MAP = {
    # Major Keys
    "b major": "1B", "bmaj": "1B",
    "f# major": "2B", "f#maj": "2B", "f sharp major": "2B",
    "gb major": "2B", "gbmaj": "2B", "g flat major": "2B",
    "c# major": "3B", "c#maj": "3B", "c sharp major": "3B",
    "db major": "3B", "dbmaj": "3B", "d flat major": "3B",
    "ab major": "4B", "abmaj": "4B", "a flat major": "4B",
    # "g# major": "4B", "g#maj": "4B", "g sharp major": "4B", # Enharmonically Ab Major
    "eb major": "5B", "ebmaj": "5B", "e flat major": "5B",
    # "d# major": "5B", "d#maj": "5B", "d sharp major": "5B", # Enharmonically Eb Major
    "bb major": "6B", "bbmaj": "6B", "b flat major": "6B",
    # "a# major": "6B", "a#maj": "6B", "a sharp major": "6B", # Enharmonically Bb Major
    "f major": "7B", "fmaj": "7B",
    "c major": "8B", "cmaj": "8B",
    "g major": "9B", "gmaj": "9B",
    "d major": "10B", "dmaj": "10B",
    "a major": "11B", "amaj": "11B",
    "e major": "12B", "emaj": "12B",

    # Minor Keys
    "g# minor": "1A", "g#min": "1A", "g#m": "1A", "g sharp minor": "1A",
    "ab minor": "1A", "abmin": "1A", "abm": "1A", "a flat minor": "1A", # Enharmonically G# minor
    "d# minor": "2A", "d#min": "2A", "d#m": "2A", "d sharp minor": "2A",
    "eb minor": "2A", "ebmin": "2A", "ebm": "2A", "e flat minor": "2A", # Enharmonically D# minor
    "a# minor": "3A", "a#min": "3A", "a#m": "3A", "a sharp minor": "3A",
    "bb minor": "3A", "bbmin": "3A", "bbm": "3A", "b flat minor": "3A", # Enharmonically A# minor
    "f minor": "4A", "fmin": "4A", "fm": "4A",
    "c minor": "5A", "cmin": "5A", "cm": "5A",
    "g minor": "6A", "gmin": "6A", "gm": "6A",
    "d minor": "7A", "dmin": "7A", "dm": "7A",
    "a minor": "8A", "amin": "8A", "am": "8A",
    "e minor": "9A", "emin": "9A", "em": "9A",
    "b minor": "10A", "bmin": "10A", "bm": "10A",
    "f# minor": "11A", "f#min": "11A", "f#m": "11A", "f sharp minor": "11A",
    "gb minor": "11A", "gbmin": "11A", "gbm": "11A", "g flat minor": "11A", # Enharmonically F# minor
    "c# minor": "12A", "c#min": "12A", "c#m": "12A", "c sharp minor": "12A",
    "db minor": "12A", "dbmin": "12A", "dbm": "12A", "d flat minor": "12A"  # Enharmonically C# minor
}

def get_camelot_key(original_key_str):
    """
    Converts a musical key string to its Camelot representation.

    Args:
        original_key_str (str): The musical key as a string (e.g., "C Major", "amin", "F#m").
                                It's recommended to provide keys in a somewhat standard format.

    Returns:
        str: The Camelot key code (e.g., "8B", "8A") or "Unknown" if the key is not found or input is invalid.
    """
    if not original_key_str or not isinstance(original_key_str, str):
        return "Unknown (Invalid input)"

    # Normalize the input string
    key = original_key_str.lower().strip()
    
    # Replace common terms for consistency with the map
    key = key.replace("sharp", "#")
    key = key.replace("flat", "b") # e.g., "g flat major" -> "gb major"

    # Attempt direct lookup first
    if key in CAMELOT_KEY_MAP:
        return CAMELOT_KEY_MAP[key]

    # Try common abbreviations if not already in map (e.g. if map only has "c major" and input was "cmaj")
    # The current map is quite comprehensive, but this can help.
    if key.endswith("maj") and not key.endswith(" major"):
        potential_key = key.replace("maj", " major")
        if potential_key in CAMELOT_KEY_MAP:
            return CAMELOT_KEY_MAP[potential_key]
    
    if key.endswith("min") and not key.endswith(" minor"):
        potential_key = key.replace("min", " minor")
        if potential_key in CAMELOT_KEY_MAP:
            return CAMELOT_KEY_MAP[potential_key]

    # Handle cases like "am", "f#m" if they weren't directly in the map
    # or if the map expects "a minor", "f# minor"
    if key.endswith("m") and not key.endswith(" minor") and not key.endswith(" major") and len(key) > 1:
        # Check if it's a simple "note + m" like "am" or "f#m"
        # Ensure it's not something like "gm" from "g major" if "g major" was somehow mis-processed
        if key[-2].isalpha() or key[-2] == '#' or key[-2] == 'b':
            potential_key = key[:-1] + " minor" # e.g. "am" -> "a minor"
            if potential_key in CAMELOT_KEY_MAP:
                return CAMELOT_KEY_MAP[potential_key]

    return "Unknown"


def add_camelot_to_song_data(song_data, original_key_field="key"):
    """
    Adds a 'camelot_key' field to a song data dictionary.

    The song_data is expected to be a dictionary representing a song's information.
    This function will read the musical key from the specified original_key_field,
    convert it to a Camelot key, and add it back to the song_data dictionary
    under the key 'camelot_key'.

    Args:
        song_data (dict): A dictionary containing the song's information.
                          Example: {'title': 'Some Song', 'artist': 'An Artist', 'key': 'C Major'}
        original_key_field (str, optional): The name of the field in song_data
                                            that contains the original musical key string.
                                            Defaults to "key".

    Returns:
        dict: The updated song_data dictionary with the 'camelot_key' field.
              If the original key is missing or conversion fails, 'camelot_key'
              will be set to "Unknown" or an error message.
              Returns the original song_data if it's not a dictionary.
    
    Side effects:
        Modifies the input song_data dictionary by adding/updating the 'camelot_key'.
    """
    if not isinstance(song_data, dict):
        # Handle cases where song_data might not be what's expected.
        # In a real application, you might log this error or raise an exception.
        print(f"Error: song_data is not a dictionary. Received: {type(song_data)}")
        return song_data 

    original_key_value = song_data.get(original_key_field)

    if original_key_value is None:
        song_data['camelot_key'] = f"Unknown (Original key field '{original_key_field}' missing)"
    elif not isinstance(original_key_value, str):
        song_data['camelot_key'] = f"Unknown (Original key '{original_key_value}' is not a string)"
    else:
        song_data['camelot_key'] = get_camelot_key(original_key_value)
        
    return song_data

# --- Example Usage ---
if __name__ == "__main__":
    # Example song data structures (dictionaries)
    song1 = {"title": "Track 1", "artist": "DJ Alpha", "key": "C Major"}
    song2 = {"title": "Track 2", "artist": "DJ Beta", "original_key_tag": "amin"} # Using a different field name
    song3 = {"title": "Track 3", "artist": "DJ Gamma", "key": "F# Minor"}
    song4 = {"title": "Track 4", "artist": "DJ Delta", "key": "Bbmaj"}
    song5 = {"title": "Track 5", "artist": "DJ Epsilon", "key": "G sharp minor"}
    song6 = {"title": "Track 6", "artist": "DJ Zeta", "key": "Dbm"} # D flat minor
    song7 = {"title": "Track 7", "artist": "DJ Eta", "key": "Not A Key"} # Invalid key
    song8 = {"title": "Track 8", "artist": "DJ Theta"} # Missing key field

    # Process the songs
    song1 = add_camelot_to_song_data(song1) # Uses default original_key_field="key"
    song2 = add_camelot_to_song_data(song2, original_key_field="original_key_tag")
    song3 = add_camelot_to_song_data(song3)
    song4 = add_camelot_to_song_data(song4)
    song5 = add_camelot_to_song_data(song5)
    song6 = add_camelot_to_song_data(song6)
    song7 = add_camelot_to_song_data(song7)
    song8 = add_camelot_to_song_data(song8)

    # Print results
    print("--- Processed Song Data with Camelot Keys ---")
    print(f"Song 1: {song1}")
    print(f"Song 2: {song2}")
    print(f"Song 3: {song3}")
    print(f"Song 4: {song4}")
    print(f"Song 5: {song5}")
    print(f"Song 6: {song6}")
    print(f"Song 7: {song7}")
    print(f"Song 8: {song8}")

    # Test get_camelot_key directly
    print("\n--- Direct get_camelot_key tests ---")
    print(f"G Major -> {get_camelot_key('G Major')}")       # Expected: 9B
    print(f"e minor -> {get_camelot_key('e minor')}")       # Expected: 9A
    print(f"f#m -> {get_camelot_key('f#m')}")               # Expected: 11A
    print(f"Db Major -> {get_camelot_key('Db Major')}")     # Expected: 3B
    print(f"d# min -> {get_camelot_key('d# min')}")         # Expected: 2A
    print(f"B maj -> {get_camelot_key('B maj')}")           # Expected: 1B
    print(f"NonExistentKey -> {get_camelot_key('NonExistentKey')}") # Expected: Unknown
    print(f"None -> {get_camelot_key(None)}") # Expected: Unknown (Invalid input)

