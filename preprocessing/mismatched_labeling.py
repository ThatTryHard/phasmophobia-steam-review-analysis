"""
This module contains experimental logic for identifying
potential sentiment mismatch reviews.

Example mismatch case:
- Steam label: Recommended
- Text sentiment: Negative
"""

NEGATIVE_KEYWORDS = [
    'bad',
    'boring',
    'broken',
    'bug',
    'terrible',
    'grindy',
    'unplayable',
    'hate',
    'refund'
]


def detect_basic_mismatch(review_text, recommendation_status):
    review_text = review_text.lower()

    negative_hits = sum(
        keyword in review_text
        for keyword in NEGATIVE_KEYWORDS
    )

    if recommendation_status == 'recommended' and negative_hits >= 2:
        return True

    return False