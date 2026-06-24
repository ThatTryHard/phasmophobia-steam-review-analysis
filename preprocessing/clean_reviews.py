import pandas as pd


def clean_reviews(df):
    """
    Basic preprocessing workflow for Steam review dataset.
    """

    # Remove duplicated reviews
    df = df.drop_duplicates(subset=['review_text'])

    # Remove missing reviews
    df = df.dropna(subset=['review_text'])

    # Normalize recommendation labels
    df['status'] = df['status'].str.strip().str.lower()

    # Remove extremely short reviews
    df = df[df['review_text'].str.len() > 10]

    return df