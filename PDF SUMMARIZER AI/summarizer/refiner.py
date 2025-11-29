"""
refiner.py
Polish Layer Protocol: Ensures outputs are clear, concise, and authoritative.
"""

import re

def refine_output(text: str) -> str:
    """
    Applies refinement passes to polish the generated output.
    - Removes redundant whitespace
    - Fixes spacing around punctuation
    - Ensures consistent headings
    - Enforces authoritative tone markers
    """
    if not text or not isinstance(text, str):
        return text

    refined = text.strip()

    # === Pass 1: Clean whitespace ===
    refined = re.sub(r'\n{3,}', '\n\n', refined)   # no more than 2 newlines
    refined = re.sub(r' +', ' ', refined)          # collapse extra spaces

    # === Pass 2: Fix punctuation spacing ===
    refined = re.sub(r'\s+([,.!?])', r'\1', refined)

    # === Pass 3: Normalize headings (### → always space after) ===
    refined = re.sub(r'^(#+)([^\s])', r'\1 \2', refined, flags=re.MULTILINE)

    # === Pass 4: Strengthen transitions (simple heuristic) ===
    refined = refined.replace("Overall,", "In conclusion,")
    refined = refined.replace("In summary,", "In conclusion,")

    # === Pass 5: Ensure authoritative closing ===
    if not refined.endswith(('.', '!', '?')):
        refined += '.'

    return refined
