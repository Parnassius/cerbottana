from __future__ import annotations

from datetime import datetime

import pytest

import databases.database as d
import utils
from database import Database
from typedefs import Role


@pytest.mark.parametrize(
    "rooms, expire_minutes, admin",
    [
        ({"room1": " ", "room2": "+"}, 30, None),
        ({"room1": " ", "room2": "+"}, 30, "%"),
        ({"room2": "+"}, 30, "+"),
        ({}, 5, "&"),
    ],
)
def test_create_token(
    rooms: dict[str, str], expire_minutes: int, admin: str | None
) -> None:
    token_id = utils.create_token(rooms, expire_minutes, admin)
    db = Database.open()
    with db.get_session() as session:
        tokens = session.query(d.Tokens).filter_by(token=token_id).all()
        room_tokens = {i.room: i.rank for i in tokens if i.room is not None}
        global_tokens = [i.rank for i in tokens if i.room is None]
        assert room_tokens == rooms
        if admin is not None:
            assert global_tokens == [admin]
        else:
            assert global_tokens == []
        for token in tokens:
            delta = datetime.utcnow() - datetime.fromisoformat(token.expiry)
            # 5 seconds should be more than enough
            assert abs(delta.total_seconds()) - expire_minutes * 60 < 5


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
        ("voice", "A", False),
        ("voice", "a", False),
        ("voice", "0", False),
        ("voice", "", False),
        ("prizewinner", "+", False),
        ("prizewinner", "^", True),
        ("driver", "§", False),
        ("voice", "§", True),
        ("driver", "Ω", False),
        ("voice", "Ω", True),
    ],
)
def test_has_role(role: Role, userrank: str, expected: bool) -> None:
    assert utils.has_role(role, userrank) == expected


@pytest.mark.parametrize(
    "uri, expected_html",
    [
        # pylint: disable=line-too-long
        ("&  <  >  \"  '", "&amp;  &lt;  &gt;  &quot;  &#x27;"),
        ("a@b.com", '<a href="mailto:a@b.com">a@b.com</a>'),
        ("mailto:a@b.com", 'mailto:<a href="mailto:a@b.com">a@b.com</a>'),
        ("a@b", "a@b"),  # Not a valid email address
        ("gOOgle.com", '<a href="http://gOOgle.com">gOOgle.com</a>'),
        ("https://google.com", '<a href="https://google.com">https://google.com</a>'),
        ("a.bcde", "a.bcde"),  # Not a valid link
        (
            "https://docs.google.com/document/d/1Qw55gu000000WMErXG_empg_BNUbYO3-3qHOau3ezR0/edit?usp=sharing/",
            '<a href="https://docs.google.com/document/d/1Qw55gu000000WMErXG_empg_BNUbYO3-3qHOau3ezR0/edit?usp=sharing/">docs.google.com/doc<small class="message-overflow">ument/d/1Qw55gu000000WMErXG_empg_BNUbYO3-3qHOau3ezR0/edit?usp=sha</small>ring/</a>',
        ),
    ],
)
def test_linkify(uri: str, expected_html: str) -> None:
    assert utils.linkify(uri) == expected_html
