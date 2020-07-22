import os, asyncio, logging, subprocess, tempfile

import requests
import send2trash as s2t
from galaxy.api.plugin import NextStep

from consts import IS_WINDOWS, DIRNAME

log = logging.getLogger(__name__)


async def get_size_at_path(start_path):
    if start_path is None:
        return None
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            await asyncio.sleep(0)
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    log.debug(f"Size: {total_size} bytes - {start_path}")
    return total_size  # in bytes


def open_path(path):
    cmd = f'"{path}"'
    if not IS_WINDOWS:
        cmd = "open " + cmd
    log.info(f"Opening: {path}")
    return run(cmd)


def run(cmd, *, shell=True):
    log.info(f"Running: {cmd}")
    return subprocess.Popen(cmd, shell=shell)


def download(url) -> str:
    log.info(f"Downloading: {url}")
    r = requests.get(url)
    download_path = os.path.join(tempfile.gettempdir(), url.split("/")[-1])
    with open(download_path, "wb") as f:
        f.write(r.content)
    return download_path


def send2trash(path):
    log.info(f"Moving to trash: {path}")
    s2t(os.path.abspath(path))


def get_next_step(
    title: str, width: int, height: int, page: str, *, end_uri_regex=".*finished.*", params=""
) -> NextStep:
    return NextStep(
        "web_session",
        {
            "window_title": title,
            "window_width": width + 20,
            "window_height": height + 30,
            "start_uri": os.path.join(DIRNAME, "page", f"{page}.html{params}"),
            "end_uri_regex": end_uri_regex,
        },
    )


def compare(x, y):
    if x is None:
        return y
    if y is None:
        return x
    return min(x, y)
