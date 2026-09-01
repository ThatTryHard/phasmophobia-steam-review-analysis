# Annotation workspace

Read `docs/ANNOTATION_GUIDE.md` before editing either CSV.

- `annotator_a_all_262.csv`: first human, every row.
- `annotator_b_blind_80.csv`: second human, independent 80-row subset that
  includes all locked-test rows.
- matching `.xlsx` files: human-friendly separate forms with dropdowns and a
  codebook; import them with the guarded `import-workbook` command.
- `adjudication_queue.csv` / `.xlsx`: the validated 10-row final-decision queue;
  only `final_*` and `adjudication_notes` are human-editable. Import a completed
  workbook with the guarded `import-adjudication-workbook` command.

Do not add Steam recommendation, playtime, keyword flags, model predictions, or
legacy labels to these files. The generator refuses to overwrite existing work
unless an explicit pre-annotation override is supplied.
