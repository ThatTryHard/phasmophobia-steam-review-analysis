# Generated dashboard data

Do not hand-edit this directory. `python -m phasma_review.cli dashboard`
generates every table from adjudicated labels and validated pipeline outputs.

The generator fails closed while annotations are incomplete. Empty model
tables mean the locked-test evaluation has not been run; they do not mean zero
errors or zero performance.
