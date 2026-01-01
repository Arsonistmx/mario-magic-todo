import json
import sys


def check_json_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Reset pointer to start to load json
        file_content = "".join(lines)
        json.loads(file_content)
        print(f"✅ SUCCESS: '{filename}' is valid JSON.")

    except json.JSONDecodeError as e:
        print(f"\n❌ ERROR in '{filename}':")
        print(f"   Message: {e.msg}")
        print(f"   Line: {e.lineno}")
        print(f"   Column: {e.colno}")

        # Show the specific line with the error
        error_line_index = e.lineno - 1
        if 0 <= error_line_index < len(lines):
            print("-" * 40)
            print(f"Line {e.lineno}: {lines[error_line_index].strip()}")
            print("-" * 40)

            # visual pointer to the error
            pointer = " " * (e.colno - 1) + "^"
            print(f"        {pointer} (Error is likely right before here)")

    except FileNotFoundError:
        print(f"❌ ERROR: The file '{filename}' was not found.")


if __name__ == "__main__":
    # You can change 'lore.json' to whatever your file is named
    filename = "lore_data.json"

    # Or allow running from command line: python3 check_json.py my_file.json
    if len(sys.argv) > 1:
        filename = sys.argv[1]

    check_json_file(filename)