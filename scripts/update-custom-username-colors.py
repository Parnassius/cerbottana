import re
import urllib.request

req = urllib.request.Request(
    "https://play.pokemonshowdown.com/config/config.js",
    headers={"User-Agent": "Mozilla"},
)
resp = urllib.request.urlopen(req)

match = re.search(r"Config\.customcolors[^;]+;", resp.read().decode("utf-8")).group(0)
match = re.sub(r"^[^\t].*$", "", match, flags=re.MULTILINE)
match = re.sub(r"\/\/.*$", "", match, flags=re.MULTILINE)

with open("../utils.py", "r+") as f:
    text = f.read()
    text = re.sub(
        r"CUSTOM_COLORS: Dict\[str, str\] = {[^}]+}",
        "CUSTOM_COLORS: Dict[str, str] = {" + match + "}",
        text,
    )
    f.seek(0)
    f.write(text)
    f.truncate()
