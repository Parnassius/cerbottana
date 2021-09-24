from domify import attribute_validators as v
from domify.html_elements import HtmlElement


class Psicon(HtmlElement):
    is_empty = True
    element_attributes = {
        "pokemon": v.str_validator,
        "item": v.str_validator,
        "type": v.str_validator,
        "category": v.str_validator,
    }


class Spotify(HtmlElement):
    element_attributes = {"src": v.str_validator}


class Twitch(HtmlElement):
    element_attributes = {"src": v.str_validator}


class Username(HtmlElement):
    element_attributes = {"name": v.str_validator}


class Youtube(HtmlElement):
    element_attributes = {"src": v.str_validator}
