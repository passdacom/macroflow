"""Packaged, side-effect-free mixed sequencer smoke contract."""

from macroflow.package_smoke import run_inline_sequence_smoke


def test_inline_sequence_package_smoke() -> None:
    run_inline_sequence_smoke()
