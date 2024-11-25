import pytest

from clean import hash128, get_path
import config
from dircheck import is_uuid


# throws an error if a path is referenced that does not exist
config.duplicates_file = ""
filestore = "/tmp"
config.filestore = filestore


@pytest.mark.parametrize(
    ["input", "expect"],
    [
        ("4259b179-557a-4e04-8c9b-e06864a15d9a", 28),
        ("aa125bf6-2023-4787-92fc-816b2c932fc5", 65),
    ],
)
def test_hash128(input, expect):
    assert hash128(input) == expect


@pytest.mark.parametrize(
    ["input", "expect"],
    [("nope", False), ("4259b179-557a-4e04-8c9b-e06864a15d9a", True)],
)
def test_is_uuid(input, expect):
    assert is_uuid(input) == expect


@pytest.mark.parametrize(
    ["input", "expect"],
    [
        (
            "4259b179-557a-4e04-8c9b-e06864a15d9a",
            "/tmp/28/4259b179-557a-4e04-8c9b-e06864a15d9a",
        ),
        (
            "d08de2ec-bc4d-46c8-b7f6-c5d243ec8027",
            "/tmp/126/d08de2ec-bc4d-46c8-b7f6-c5d243ec8027",
        ),
    ],
)
def test_get_path(input, expect):
    assert get_path(input) == expect
