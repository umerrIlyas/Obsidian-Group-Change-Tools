"""HexColor validation + normalise_hex."""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from changetools.domain.brand import Neutrals, normalise_hex


def test_normalise_three_digit_hex() -> None:
    assert normalise_hex("#abc") == "#AABBCC"


def test_normalise_six_digit_hex_uppercases() -> None:
    assert normalise_hex("#0d171e") == "#0D171E"


def test_normalise_invalid_hex_raises() -> None:
    with pytest.raises(ValueError, match="Invalid hex"):
        normalise_hex("not-a-color")


def test_neutrals_default_when_unset() -> None:
    n = Neutrals()
    assert n.stone == "#6B7280"
    assert n.hairline == "#D9DEE3"
    assert n.fog == "#EEF1F3"


def test_neutrals_rejects_bad_hex() -> None:
    with pytest.raises(PydanticValidationError):
        Neutrals(stone="banana")  # type: ignore[arg-type]
