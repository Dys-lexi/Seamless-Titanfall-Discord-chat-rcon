import os
import re

def strip_leading_numbers(directory):
    for filename in os.listdir(directory):
        old_path = os.path.join(directory, filename)
        if os.path.isfile(old_path):
            # Use regex to strip leading numbers and optional separators
            new_filename = re.sub(r'^\d+[\s_]*', '', filename)
            new_path = os.path.join(directory, new_filename)
            if old_path != new_path:
                os.rename(old_path, new_path)
                print(f"Renamed: {filename} -> {new_filename}")

# Example usage
strip_leading_numbers('./')
