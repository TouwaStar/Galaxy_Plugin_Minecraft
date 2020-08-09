import os, logging

from galaxy.api.plugin import GameTime

from consts import IS_WINDOWS, GameID
import utils

log = logging.getLogger(__name__)


class PathNotExectuable(Exception):
    pass


class MultiMCClient:
    def __init__(self, path: str):
        self.path = os.path.expanduser(os.path.expandvars(os.path.abspath(path)))
        if not os.access(path, os.X_OK):
            raise PathNotExectuable
        self.folder = os.path.dirname(self.path) if IS_WINDOWS else self.path
        log.debug(f"MultiMC Path: {self.path}")
        self.instances_path = (
            os.path.join(self.folder, "instances")
            if IS_WINDOWS
            else os.path.join(self.folder, "Contents", "MacOS", "instances")
        )
        log.debug(f"MultiMC instances path: {self.instances_path}")
        self.process = None

    def get_time(self):
        time = 0  # in seconds
        lastPlayed = None
        for f in os.scandir(self.instances_path):
            if f.is_dir():
                cfg_path = os.path.join(f.path, "instance.cfg")
                if os.path.isfile(cfg_path):
                    with open(cfg_path, "r") as f:
                        for line in f.readlines():
                            split_line = line.strip().split("=")
                            if split_line[0] == "totalTimePlayed":
                                time += int(split_line[1])
                            elif split_line[0] == "lastLaunchTime":
                                lastPlayed = utils.compare(lastPlayed, int(split_line[1]))
        log.debug(f"Got total MultiMC Time: {time / 60}")
        return GameTime(GameID, time / 60, lastPlayed)

    def launch(self):
        self.process = utils.open_path(self.path)

    def running(self):
        if self.process is None:
            return False
        elif self.process.poll() is None:
            return True
        else:
            self.process = None
            return False
