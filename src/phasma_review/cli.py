"""Command-line entry point for the gated research pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .analysis import run_analysis
from .annotations import (
    annotation_status,
    build_adjudication_queue,
    finalize_labels,
    import_adjudication_workbook,
    import_annotation_workbook,
)
from .dashboard import run_dashboard
from .external_validation import validate_external_set, write_external_template
from .modeling import run_modeling
from .prepare import migrate_and_prepare, prepare_from_sanitized_source
from .schema import AnnotationIncompleteError


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="phasma-review",
        description="Blinded annotation and reproducible review analysis",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    migrate = subparsers.add_parser(
        "migrate-legacy",
        help="One-time privacy-safe migration of the original raw CSV.",
    )
    migrate.add_argument("legacy_path", type=Path)
    migrate.add_argument("--overwrite-annotations", action="store_true")

    prepare = subparsers.add_parser(
        "prepare-annotations",
        help="Recreate blank blinded templates from the sanitized source.",
    )
    prepare.add_argument("--overwrite-annotations", action="store_true")

    subparsers.add_parser("status", help="Show annotation/evidence-gate status.")
    import_workbook = subparsers.add_parser(
        "import-workbook",
        help="Validate a completed Excel form and update its canonical CSV.",
    )
    import_workbook.add_argument("workbook_path", type=Path)
    import_workbook.add_argument("--annotator", choices=("a", "b"), required=True)
    import_workbook.add_argument("--allow-less-complete", action="store_true")
    subparsers.add_parser(
        "build-adjudication",
        help="Compute independent agreement and write disagreement queue.",
    )
    import_adjudication = subparsers.add_parser(
        "import-adjudication-workbook",
        help="Validate final decisions in the Excel queue and update its CSV.",
    )
    import_adjudication.add_argument("workbook_path", type=Path)
    subparsers.add_parser(
        "finalize-labels",
        help="Validate adjudication and write the only downstream label table.",
    )
    subparsers.add_parser("analyze", help="Run full-corpus descriptive analysis.")
    model = subparsers.add_parser(
        "model",
        help="Run development CV and the planned locked-test evaluation.",
    )
    model.add_argument("--cv-repeats", type=int, default=10)
    subparsers.add_parser("dashboard", help="Build audited tables and HTML dashboard.")
    subparsers.add_parser(
        "external-template",
        help="Create the schema-only future-update validation template.",
    )
    external = subparsers.add_parser(
        "validate-external",
        help="Evaluate a genuinely later independently annotated dataset.",
    )
    external.add_argument("--minimum-rows", type=int, default=100)
    run_all = subparsers.add_parser(
        "run-all",
        help="Finalize labels, analyze, model, and build dashboard in dependency order.",
    )
    run_all.add_argument("--cv-repeats", type=int, default=10)
    return parser


def _main_unhandled(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "migrate-legacy":
        source = migrate_and_prepare(
            args.legacy_path,
            overwrite_annotations=args.overwrite_annotations,
        )
        print(f"Prepared {len(source)} deidentified rows and blinded templates.")
    elif args.command == "prepare-annotations":
        source = prepare_from_sanitized_source(
            overwrite_annotations=args.overwrite_annotations
        )
        print(f"Prepared blinded templates for {len(source)} rows.")
    elif args.command == "status":
        print(json.dumps(annotation_status(), indent=2, sort_keys=True))
    elif args.command == "import-workbook":
        imported = import_annotation_workbook(
            args.workbook_path,
            args.annotator,
            allow_less_complete=args.allow_less_complete,
        )
        print(f"Imported {len(imported)} rows for Annotator {args.annotator.upper()}.")
    elif args.command == "build-adjudication":
        queue = build_adjudication_queue()
        print(f"Adjudication queue contains {len(queue)} rows.")
    elif args.command == "import-adjudication-workbook":
        imported = import_adjudication_workbook(args.workbook_path)
        print(f"Imported final decisions for {len(imported)} adjudication rows.")
    elif args.command == "finalize-labels":
        final = finalize_labels()
        print(f"Finalized {len(final)} adjudicated labels.")
    elif args.command == "analyze":
        outputs = run_analysis()
        print(f"Analyzed {len(outputs['featured'])} full-corpus rows.")
    elif args.command == "model":
        result = run_modeling(repeats=args.cv_repeats)
        print(f"Selected model: {result['selected_model']}")
    elif args.command == "dashboard":
        tables = run_dashboard()
        print(f"Built {len(tables)} audited dashboard tables.")
    elif args.command == "external-template":
        write_external_template()
        print("External validation template is ready.")
    elif args.command == "validate-external":
        result = validate_external_set(minimum_rows=args.minimum_rows)
        print(result.to_string(index=False))
    elif args.command == "run-all":
        final = finalize_labels()
        run_analysis()
        result = run_modeling(repeats=args.cv_repeats)
        run_dashboard()
        print(
            f"Completed {len(final)} labeled rows; selected {result['selected_model']}."
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    """Return a concise blocked status instead of exposing a stack trace."""

    try:
        return _main_unhandled(argv)
    except (
        AnnotationIncompleteError,
        FileNotFoundError,
        FileExistsError,
        ValueError,
    ) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
