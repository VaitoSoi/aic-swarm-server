import copy
import http
import logging
import os
import sys
import typing
from os import path

import click
import tqdm

import json as json_


def read_json(file) -> dict[str, str]:
    with open(file, "r") as file:
        return json_.load(file)


def write_json(file, data: dict[str, str]) -> None:
    with open(file, "w") as file:
        json_.dump(data, file, indent=4)


temp = path.abspath("temp")
data = path.abspath("data")
mirror = path.abspath("mirror")
objects = path.abspath("objects")
base_url = "https://atm249495-s3user.vcos.cloudstorage.com.vn/aic24-b5/"

os.mkdir(temp) if not os.path.exists(temp) else None
os.mkdir(data) if not os.path.exists(data) else None
os.mkdir(mirror) if not os.path.exists(mirror) else None
os.mkdir(objects) if not os.path.exists(objects) else None

keyframes = path.join(data, "keyframes")
clip_features = path.join(data, "clip_features")

keyframes_mirror = path.join(mirror, "keyframes.json")
keyframes_mirror_json = read_json(keyframes_mirror)
clip_features_mirror = path.join(mirror, "clip_features.txt")
clip_features_mirror_url = open(clip_features_mirror, "r").read().splitlines()[0]


class ColorizedFormatter(logging.Formatter):
    level_name_colors = {
        logging.DEBUG: lambda level_name: click.style(str(level_name), fg="cyan"),
        logging.INFO: lambda level_name: click.style(str(level_name), fg="bright_blue"),
        logging.WARNING: lambda level_name: click.style(str(level_name), fg="bright_yellow"),
        logging.ERROR: lambda level_name: click.style(str(level_name), fg="bright_red"),
        logging.CRITICAL: lambda level_name: click.style(str(level_name), fg="red"),
    }

    def __init__(
            self,
            fmt: str | None = None,
            datefmt: str | None = None,
            style: typing.Literal["%", "{", "$"] = "%",
            use_colors: bool | None = None,
    ):
        if use_colors in (True, False):
            self.use_colors = use_colors
        else:
            self.use_colors = sys.stdout.isatty()
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)

    def color_level_name(self, level_name: str, level_no: int) -> str:
        def default(level_name: str) -> str:
            return str(level_name)  # pragma: no cover

        func = self.level_name_colors.get(level_no, default)
        return func(level_name)

    def formatMessage(self, record):
        recordcopy = copy.copy(record)
        levelname = f"{recordcopy.levelname:<7}"
        if self.use_colors:
            levelname = self.color_level_name(levelname, recordcopy.levelno)
        recordcopy.__dict__["levelname"] = levelname
        return super().formatMessage(recordcopy)


class AccessFormatter(ColorizedFormatter):
    @staticmethod
    def phrase_color(status_code: int, message: str) -> str:
        if http.HTTPStatus(status_code).is_redirection:
            return click.style(str(message), fg="bright_white")
        if http.HTTPStatus(status_code).is_success:
            return click.style(str(message), fg="green")
        if http.HTTPStatus(status_code).is_informational:
            return click.style(str(message), fg="yellow")
        if http.HTTPStatus(status_code).is_client_error:
            return click.style(str(message), fg="red")
        if http.HTTPStatus(status_code).is_server_error:
            return click.style(str(message), fg="bright_red")

    def formatMessage(self, record):
        recordcopy = copy.copy(record)
        (
            client_addr,
            method,
            full_path,
            http_version,
            status_code,
        ) = recordcopy.args
        status_code_phrase = None
        try:
            status_code_phrase = http.HTTPStatus(status_code).phrase
        except ValueError:
            status_code_phrase = ""
        request_line = f"{method} {full_path} HTTP/{http_version}"
        recordcopy.__dict__["message"] = \
            f'{client_addr} - "{request_line}" {self.phrase_color(status_code, f"{status_code} {status_code_phrase}")}'

        return super().formatMessage(recordcopy)


class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.tqdm.write(msg)
            self.flush()
        except Exception:
            self.handleError(record)


def formatter(name: str, formatter_: logging.Formatter = ColorizedFormatter):
    return formatter_(  # noqa
        f"%(asctime)s :: {name:<{10}} :: %(levelname)-7s :: %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )


def handler(name: str, formatter_: logging.Formatter = ColorizedFormatter):
    handler = TqdmLoggingHandler()
    handler.setFormatter(formatter(name, formatter_))
    return handler
