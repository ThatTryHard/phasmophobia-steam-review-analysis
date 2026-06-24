import re


def extract_playtime(playtime_text):
    """
    Convert Steam playtime string into float hours.

    Example:
    "12.5 hrs on record" -> 12.5
    "0.3 hrs" -> 0.3
    """

    match = re.search(r'(\d+\.?\d*)', playtime_text)

    if match:
        return float(match.group(1))

    return 0.0


def safe_locator_text(locator, default="N/A"):
    """
    Safely extract locator text.
    """

    try:
        return locator.inner_text().strip()

    except:
        return default
