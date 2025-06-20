from __future__ import annotations

import asyncio
import random
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import TYPE_CHECKING, ClassVar

from domify import html_elements as e
from domify.base_element import BaseElement
from PIL import Image

from cerbottana import custom_elements as ce
from cerbottana import utils
from cerbottana.models.room import Room
from cerbottana.plugins import command_wrapper
from cerbottana.tasks import background_task_wrapper

if TYPE_CHECKING:
    from cerbottana.connection import Connection
    from cerbottana.models.message import Message, RawMessage

images_dir = utils.get_config_file("images")
images_cropped_dir = utils.get_config_file("images_cropped")


def get_random_pokemon() -> Path:
    if random.randint(1, 128) == 128:
        path = images_dir / "shiny"
    else:
        path = images_dir / "regular"

    subdirs = list(path.iterdir())
    path = random.choice(subdirs)

    subdirs = list(path.iterdir())
    path = random.choice(subdirs)

    if path.is_dir():
        subdirs = list(path.iterdir())
        path = random.choice(subdirs)

    return path


def crop_and_save(game: Game, size: int) -> Path:
    with Image.open(game.path) as im:
        half_crop = round(min(im.width, im.height) / 10 * 1.5**size) // 2
        if not game.crop_origin:
            # If the crop origin has not yet been decided (first crop), then get
            # random origin coordinates and crop the image to the required size
            while True:
                origin_x = random.randint(half_crop, im.width - half_crop)
                origin_y = random.randint(half_crop, im.height - half_crop)
                im_cropped = im.crop(
                    (
                        origin_x - half_crop,
                        origin_y - half_crop,
                        origin_x + half_crop,
                        origin_y + half_crop,
                    )
                )
                # Try again if there are little to no opaque pixels
                opaque_pixels = sum(
                    1 for alpha in im_cropped.getchannel("A").getdata() if alpha == 255
                )
                if opaque_pixels > im_cropped.width * im_cropped.height * 0.25:
                    break

                # Save the coordinates for subsequent crops
            game.crop_origin = origin_x, origin_y

        else:
            # Get the saved coordinates, clamping them to avoid going out of bounds
            origin_x, origin_y = game.crop_origin
            origin_x = max(half_crop, min(origin_x, im.width - half_crop))
            origin_y = max(half_crop, min(origin_y, im.height - half_crop))
            im_cropped = im.crop(
                (
                    origin_x - half_crop,
                    origin_y - half_crop,
                    origin_x + half_crop,
                    origin_y + half_crop,
                )
            )

    filename = f"{secrets.token_urlsafe(8)}.png"
    cropped_path = images_cropped_dir / filename
    im_cropped.save(cropped_path)
    return cropped_path


def get_image(path: Path, base_url: str) -> BaseElement:
    with Image.open(path) as im:
        width, height = im.size
    if width > 256:
        ratio = height / width
        width = 256
        height = int(256 * ratio)
    relative_path = path.relative_to(utils.get_config_file(""))
    url = f"{base_url}/{relative_path}"
    return e.Img(src=url, width=width, height=height)


@dataclass
class Game:
    pokemon: str
    path: Path
    crop_origin: tuple[int, int] | None = None
    finish_event: asyncio.Event = field(default_factory=asyncio.Event)


@command_wrapper(
    aliases=("gts", "gtz"),
    helpstr="Indovina un pokemon da zoom progressivamente sempre più rivelatori!",
    allow_pm=False,
    required_rank_editable=True,
    single_instance=True,
)
class GuessTheSprite:
    active_games: ClassVar[dict[Room, Game]] = {}

    @classmethod
    async def cmd_func(cls, msg: Message) -> None:
        if msg.room is None:
            return

        full_pokemon_path = get_random_pokemon()
        relative_path = full_pokemon_path.relative_to(images_dir)
        pokemon = relative_path.parts[1]
        game = Game(pokemon, full_pokemon_path)
        cls.active_games[msg.room] = game

        for size in range(4):
            if msg.room not in cls.active_games:
                return

            cropped_path = crop_and_save(game, size)
            html = get_image(cropped_path, msg.conn.base_url)
            await msg.reply_htmlbox(html)
            try:
                await asyncio.wait_for(game.finish_event.wait(), 10)
            except TimeoutError:
                # Timeout expired, go to the next image
                pass
            else:
                # The pokemon has been guessed
                return

        if msg.room in cls.active_games:
            del cls.active_games[msg.room]
            ps_dex_entry = utils.get_ps_dex_entry(game.pokemon)
            name = ps_dex_entry["name"] if ps_dex_entry else game.pokemon
            html = (
                get_image(game.path, msg.conn.base_url)
                + e.Br()
                + "Nessuno ha vinto, era "
                + e.Strong(name)
                + "!"
            )
            await msg.reply_htmlbox(html)

    @classmethod
    async def on_message(cls, msg: RawMessage) -> None:
        if msg.room is None:
            return

        message = utils.to_id(utils.remove_diacritics(msg.message))
        game = cls.active_games.get(msg.room)
        if game and game.pokemon == message:
            del cls.active_games[msg.room]
            game.finish_event.set()
            ps_dex_entry = utils.get_ps_dex_entry(game.pokemon)
            name = ps_dex_entry["name"] if ps_dex_entry else game.pokemon
            html = (
                get_image(game.path, msg.conn.base_url)
                + e.Br()
                + ce.Username(msg.user.username)
                + " ha vinto, era "
                + e.Strong(name)
                + "!"
            )
            await msg.reply_htmlbox(html)


@background_task_wrapper()
async def remove_old_cropped_images(conn: Connection) -> None:  # noqa: ARG001
    await asyncio.sleep(1 * 60 * 60)

    while True:
        cutoff_time = time() - 3 * 24 * 60 * 60  # 3 days
        for img in images_cropped_dir.iterdir():
            try:
                if img.is_file() and img.stat().st_mtime < cutoff_time:
                    img.unlink()
            except FileNotFoundError:
                continue

        await asyncio.sleep(24 * 60 * 60)
