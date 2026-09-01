# Research model artifacts

The completed internal evidence gates produced `sentiment_pipeline.joblib` and
`model_manifest.json` here. Re-running `run-all` reproduces them from the
finalized labels and immutable development/test partition.

The manifest always marks the artifact research-only and leaves the operational
abstention threshold unset. A generated artifact is not production approval.
