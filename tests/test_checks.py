import pytest

from envkeep.checks import check_type


@pytest.mark.parametrize(
    ("type_name", "value"),
    [
        ("int", "0"),
        ("int", "-42"),
        ("int", "+7"),
        ("float", "3.14"),
        ("float", "-.5"),
        ("float", "1e-3"),
        ("float", "10"),
        ("bool", "true"),
        ("bool", "FALSE"),
        ("bool", "yes"),
        ("bool", "0"),
        ("url", "postgres://u:p@localhost:5432/app"),
        ("url", "https://example.com/path?x=1"),
        ("url", "redis://localhost:6379"),
        ("str", "anything at all"),
        ("url", "http://localhost:80"),
        ("url", "http://user:pass@host:8080/path"),
        ("url", "http://127.0.0.1:8000"),
        ("url", "http://[::1]:8080"),
    ],
)
def test_valid_values(type_name, value):
    assert check_type(type_name, value) is None


@pytest.mark.parametrize(
    ("type_name", "value"),
    [
        ("int", "abc"),
        ("int", "1.5"),
        ("int", "1_000"),
        ("int", " 5"),
        ("int", "١٢٣"),
        ("float", "nan"),
        ("float", "inf"),
        ("float", "1.2.3"),
        ("float", "."),
        ("bool", "maybe"),
        ("bool", "2"),
        ("url", "example.com"),
        ("url", "localhost:5432"),
        ("url", "http://"),
        ("url", "not a url"),
        ("url", "http:/x"),
        ("url", "https://exa mple.com"),
        ("url", "http://host:99999"),
        ("url", "http://host:abc"),
        ("url", "http://:80"),
        ("url", "http://:80/path"),
        ("url", "postgres://u:p@:5432/db"),
        ("url", "http://@"),
    ],
)
def test_invalid_values(type_name, value):
    assert check_type(type_name, value) is not None


def test_problem_message_never_contains_the_value():
    assert "supersecret" not in check_type("int", "supersecret")
