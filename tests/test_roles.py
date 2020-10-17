import pytest

from typedefs import Role
from utils import has_role


@pytest.mark.parametrize(
    "role, userrank, expected",
    [
        ("admin", "~", True),
        ("admin", "&", True),
        ("admin", "*", False),
        ("admin", "", False),
        ("owner", "&", True),
        ("owner", "#", True),
        ("owner", "*", False),
        ("bot", "#", False),
        ("bot", "*", True),
        ("bot", "★", False),
        ("host", "*", False),
        ("host", "★", True),
        ("host", "@", False),
        ("mod", "#", True),
        ("mod", "*", False),
        ("mod", "★", False),
        ("mod", "@", True),
        ("mod", "%", False),
        ("driver", "*", False),
        ("driver", "★", False),
        ("driver", "@", True),
        ("driver", "%", True),
        ("driver", "+", False),
        ("player", "%", False),
        ("player", "☆", True),
        ("player", "+", False),
        ("voice", "*", False),
        ("voice", "★", False),
        ("voice", "%", True),
        ("voice", "☆", False),
        ("voice", "+", True),
        ("voice", "^", False),
        ("voice", " ", False),
        ("voice", "", False),
        ("prizewinner", "+", False),
        ("prizewinner", "^", True),
        ("driver", "§", False),
        ("voice", "§", True),
    ],
)
def test_role(role: Role, userrank: str, expected: bool) -> None:
    assert has_role(role, userrank) == expected
