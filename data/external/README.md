# Future-update external validation

`future_update_reviews.csv` is a schema-only contract, not evidence. Populate it
with a newly collected, independently and blindly annotated review set only
after the source collection window.

Do not annotate in this merged file because it exposes Steam recommendation.
First create separate text-only files for two human annotators, adjudicate them
under `docs/ANNOTATION_GUIDE.md`, and only then merge the final labels with
metadata. Set `annotation_protocol_version` to `v2_blind` and
`annotation_source` to `human_agreed` or `human_adjudicated`; the validator
rejects single-coded rows.

The validation gate requires at least 100 eligible English/sufficient rows,
every review date later than the original maximum date, no exact normalized
text overlap with the original corpus, and complete human labels with unique
external IDs.

Run `python -m phasma_review.cli validate-external`. Passing this code-level
gate does not itself authorize production deployment.
