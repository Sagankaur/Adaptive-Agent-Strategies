from pathlib import Path


def test_model_created_exact_requested_file() -> None:
    output = Path("/app/output.txt")
    assert output.is_file(), "model did not create /app/output.txt"
    assert output.read_bytes() == b"harbor smoke passed\n"
