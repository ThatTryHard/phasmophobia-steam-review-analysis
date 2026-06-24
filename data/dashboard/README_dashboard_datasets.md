# Dashboard Dataset Guide

This folder contains dashboard-ready CSV files for the Steam Review Sentiment Mismatch project.

## Main Files

### dashboard_review_level.csv
One row per tagged review. Use this as the main dashboard table.

Recommended charts:
- Recommendation vs manual sentiment
- Mismatch group distribution
- Playtime segment vs sentiment
- Theme flags by recommendation
- Review examples table

### dashboard_kpi_summary.csv
KPI card dataset.

Suggested cards:
- Total tagged reviews
- Recommended review percentage
- Negative sentiment percentage
- Mixed / ambiguous percentage
- Soft mismatch percentage
- Update-related review percentage
- Mourning review percentage

### dashboard_recommendation_sentiment_matrix.csv
Use for stacked bar charts comparing Steam recommendation labels against manual sentiment.

### dashboard_mismatch_summary.csv
Use for mismatch distribution charts.

### dashboard_mismatch_by_recommendation.csv
Use for showing which Steam recommendation labels contain more ambiguity or mismatch.

### dashboard_category_summary.csv
Use for explaining why reviews are positive, negative, mixed, or ambiguous.

### dashboard_player_sentiment_summary.csv
Use for showing sentiment distribution by playtime segment.

### dashboard_player_mismatch_summary.csv
Use for showing mismatch / ambiguity by playtime segment.

### dashboard_theme_summary.csv
Use for update, bug, emotion, mourning, and low-information theme cards.

### dashboard_theme_by_recommendation.csv
Use for comparing theme rates between Recommended and Not Recommended reviews.

### dashboard_model_summary.csv
Use for model performance KPI cards.

### dashboard_error_examples_clean.csv
Use for explaining model limitations and multiclass errors.

### dashboard_representative_examples.csv
Use for dashboard text cards or report examples.

## Suggested Dashboard Pages

### Page 1: Executive Overview
- KPI cards
- Recommendation distribution
- Manual sentiment distribution
- Recommendation vs manual sentiment stacked bar

### Page 2: Player Behavior
- Playtime segment vs sentiment
- Playtime segment vs mismatch
- Review length by sentiment
- Veteran / Hardcore review behavior

### Page 3: Mismatch & Ambiguity
- Mismatch group distribution
- Mismatch by recommendation
- Category summary
- Representative soft mismatch examples

### Page 4: Model Performance
- Binary model KPI
- Multiclass model KPI
- Error type distribution
- Error examples

## Main Interpretation

Steam recommendation labels are useful for coarse positive/negative polarity, but they do not fully capture mixed sentiment, ambiguous review behavior, joke reviews, or positive recommendations that still contain complaints.