from __future__ import annotations

import pytest

from cerbottana import utils
from cerbottana.typedefs import Role


@pytest.mark.parametrize(
    "role, userrank, expected",
    [
        ("admin", "~", True),
        ("admin", "&", True),
        ("admin", "*", False),
        ("admin", "", False),
        ("sectionleader", "§", True),
        ("sectionleader", "#", False),
        ("owner", "&", True),
        ("owner", "#", True),
        ("owner", "§", False),
        ("owner", "*", False),
        ("bot", "#", False),
        ("bot", "*", True),
        ("bot", "★", False),
        ("host", "*", False),
        ("host", "★", True),
        ("host", "@", False),
        ("mod", "#", True),
        ("mod", "§", True),
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
        ("voice", "A", False),
        ("voice", "a", False),
        ("voice", "0", False),
        ("voice", "", False),
        ("prizewinner", "+", False),
        ("prizewinner", "^", True),
        ("driver", "-", False),
        ("voice", "-", True),
        ("driver", "Ω", False),
        ("voice", "Ω", True),
    ],
)
def test_has_role(role: Role, userrank: str, expected: bool) -> None:
    assert utils.has_role(role, userrank) == expected
