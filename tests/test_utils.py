"""Tests for deterministic cross-platform utilities."""

import tempfile
import unittest
from pathlib import Path

from phasma_review.utils import sha256_file, sha256_text_file


class HashingTests(unittest.TestCase):
    def test_text_hash_ignores_platform_line_endings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            lf_path = Path(directory) / "lf.csv"
            crlf_path = Path(directory) / "crlf.csv"
            lf_path.write_bytes(b"id,label\n1,Positive\n")
            crlf_path.write_bytes(b"id,label\r\n1,Positive\r\n")

            self.assertNotEqual(sha256_file(lf_path), sha256_file(crlf_path))
            self.assertEqual(
                sha256_text_file(lf_path),
                sha256_text_file(crlf_path),
            )
