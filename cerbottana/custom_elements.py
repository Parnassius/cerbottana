from domify import validators as v
from domify.html_elements import HtmlElement


class Psicon(HtmlElement):
    is_empty = True
    element_attributes = {
        "pokemon": v.attribute_str,
        "item": v.attribute_str,
        "type": v.attribute_str,
        "category": v.attribute_str,
    }


class Spotify(HtmlElement):
    element_attributes = {"src": v.attribute_str}


class Twitch(HtmlElement):
    element_attributes = {"src": v.attribute_str}


class Username(HtmlElement):
    element_attributes = {"name": v.attribute_str}


class Youtube(HtmlElement):
    element_attributes = {"src": v.attribute_str}
