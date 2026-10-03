from pathlib import Path

text = Path("raw_extracted.txt").read_text(encoding="utf-8")

# Show the first 150 lines exactly as Python sees them
lines = text.splitlines()

for i, line in enumerate(lines[:150], start=1):
    print(f"{i:03}: {repr(line)}")