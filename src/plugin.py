import sys, asyncio, logging, urllib, os, json, pickle
from galaxy.api.plugin import (
    Plugin,
    LocalGame,
    Authentication,
    Game,
    create_and_run_plugin,
    NextStep,
)
from galaxy.api.consts import LocalGameState, LicenseType, OSCompatibility, Platform
from galaxy.api.types import LicenseInfo
from galaxyutils import time_tracker

from local import WindowsLocalClient, MacLocalClient
from consts import (
    GameID,
    MINECRAFT_DUNGEONS_INSTALL_URL,
    MINECRAFT_MAC_INSTALL_URL,
    MINECRAFT_WIN_INSTALL_URL,
    GAME_NAMES,
    IS_WINDOWS,
    INSTALLED_FOLDER_PATH,
    DIRNAME,
)
import utils
from version import __version__


log = logging.getLogger(__name__)


class MinecraftPlugin(Plugin):
    def __init__(self, reader, writer, token):
        super().__init__(Platform.Minecraft, __version__, reader, writer, token)
        self.local_client = WindowsLocalClient() if IS_WINDOWS else MacLocalClient()
        self.status = {
            GameID.Minecraft: LocalGameState.None_,
            GameID.MinecraftDungeons: LocalGameState.None_,
        }
        self.was_game_launched_task: asyncio.Task = None
        self.update_task: asyncio.Task = None
        self.check_sizes_task: asyncio.Task = None
        self.owned = []

    async def authenticate(self, stored_credentials=None):
        if stored_credentials is not None and "owned" in stored_credentials.keys():
            self.owned = stored_credentials["owned"]
            return Authentication("mojang_user", "Mojang User")
        return NextStep(
            # May have taken some inspiration from FriendsOfGalaxy's steam integration. ;)
            "web_session",
            {
                "window_title": "Select Owned Games",
                "window_width": 720,
                "window_height": 720,
                "start_uri": os.path.join(DIRNAME, "page", "index.html"),
                "end_uri_regex": ".*finished.*",
            },
        )

    async def pass_login_credentials(self, step, credentials, cookies):
        params = urllib.parse.parse_qs(urllib.parse.urlsplit(credentials["end_uri"]).query)
        log.debug(f"Params: {params}")
        for game_id in params.keys():
            if game_id in [GameID.Minecraft, GameID.MinecraftDungeons]:
                self.owned.append(game_id)
        self.store_credentials({"owned": self.owned})
        return Authentication("mojang_user", "Mojang User")

    async def get_owned_games(self):
        log.debug(f"self.owned: {self.owned}")
        out = []
        for game_id in self.owned:
            out.append(
                Game(game_id, GAME_NAMES[game_id], None, LicenseInfo(LicenseType.SinglePurchase))
            )
        return out

    async def get_local_games(self):
        local_games = []
        for game_id in self.owned:
            local_games.append(LocalGame(game_id, self.status[game_id]))
        return local_games

    async def get_os_compatibility(self, game_id, context):
        # Assuming OS compatible with game and supported by this plugin.
        if game_id == GameID.Minecraft:
            return OSCompatibility.MacOS | OSCompatibility.Windows
        elif game_id == GameID.MinecraftDungeons:
            return OSCompatibility.Windows

    async def prepare_local_size_context(self, game_ids):
        sizes = []
        for game_id in game_ids:
            sizes.append(
                await utils.get_size_at_path(
                    self.local_client.find_launcher_path(game_id, folder=True)
                )
            )
        return dict(zip(game_ids, sizes))

    async def get_local_size(self, game_id: str, context):
        return context[game_id]

    async def install_game(self, game_id):
        if game_id == GameID.Minecraft:
            url = MINECRAFT_WIN_INSTALL_URL if IS_WINDOWS else MINECRAFT_MAC_INSTALL_URL
        elif game_id == GameID.MinecraftDungeons:
            url = MINECRAFT_DUNGEONS_INSTALL_URL
        else:
            log.warning(f"Uknown game_id to install: {game_id}")
            return
        installer_path = utils.download(url)
        log.info(f"Installing {game_id} by launching: {installer_path}")
        utils.open_path(installer_path)

    async def launch_game(self, game_id):
        log.info(f"Launching {game_id}")
        utils.open_path(self.local_client.find_launcher_path(game_id))

    async def uninstall_game(self, game_id):
        log.info(f"Uninstalling {game_id}")
        self.local_client.uninstall(game_id)

    async def _update(self):
        if self.was_game_launched_task is None or self.was_game_launched_task.done():
            self.was_game_launched_task = self.create_task(
                self.local_client.was_game_launched(), "Was Game Launched Task"
            )
        for game_id in self.owned:
            pth = self.local_client.find_launcher_path(game_id)
            if (
                self.local_client.is_game_still_running(game_id)
                and self.status[game_id] != LocalGameState.Installed | LocalGameState.Running
            ):
                log.debug(f"Starting to track time for {game_id}")
                self.game_time_tracker.start_tracking_game(game_id)
                self.status[game_id] = LocalGameState.Installed | LocalGameState.Running
                self.update_local_game_status(LocalGame(game_id, self.status[game_id]))
            elif (
                not self.local_client.is_game_still_running(game_id)
                and pth is not None
                and self.status[game_id] != LocalGameState.Installed
            ):
                try:
                    self.game_time_tracker.stop_tracking_game(game_id)
                    log.debug(f"Stopped tracking time for {game_id}")
                except time_tracker.GameNotTrackedException:
                    pass
                self.status[game_id] = LocalGameState.Installed
                self.update_local_game_status(LocalGame(game_id, self.status[game_id]))
            elif pth is None and self.status[game_id] != LocalGameState.None_:
                self.status[game_id] = LocalGameState.None_
                self.update_local_game_status(LocalGame(game_id, self.status[game_id]))
        log.debug(f"game status: {self.status}")
        await asyncio.sleep(0)

    def tick(self):
        if self.update_task is None or self.update_task.done():
            self.update_task = self.create_task(self._update(), "Update Task")

    # Time Tracker

    async def get_game_time(self, game_id, context):
        try:
            time = self.game_time_tracker.get_tracked_time(game_id)
        except time_tracker.GameNotTrackedException:
            time = None
        log.debug(f"Got game time: {time}")
        return time

    def handshake_complete(self):
        self.play_time_cache_path = os.path.join(
            INSTALLED_FOLDER_PATH, "minecraft_play_time_cache.txt"
        )
        log.debug(f"Local Play Time Cache Path: {self.play_time_cache_path}")
        if "game_time_cache" in self.persistent_cache:
            self.game_time_cache = pickle.loads(
                bytes.fromhex(self.persistent_cache["game_time_cache"])
            )
        else:
            try:
                file = open(self.play_time_cache_path, "r")
                for line in file.readlines():
                    if line[:1] != "#":
                        self.game_time_cache = pickle.loads(bytes.fromhex(line))
                        break
            except FileNotFoundError:
                self.game_time_cache = None
        self.game_time_tracker = time_tracker.TimeTracker(game_time_cache=self.game_time_cache)

    async def shutdown(self):
        if self.game_time_cache is not None:
            with open(self.play_time_cache_path, "w+") as file:
                file.write("# DO NOT EDIT THIS FILE\n")
                file.write(self.game_time_tracker.get_time_cache_hex())
                log.info("Wrote to local file cache")
        await super().shutdown()

    def game_times_import_complete(self):
        try:
            self.game_time_cache = self.game_time_tracker.get_time_cache()
            log.debug(f"game_time_cache: {self.game_time_cache}")
            self.persistent_cache["game_time_cache"] = self.game_time_tracker.get_time_cache_hex()
            self._connection.send_notification(
                "push_cache", params={"data": self._persistent_cache}
            )  # push cache without marking it sensitive (better for debug)
        except time_tracker.GamesStillBeingTrackedException:
            log.debug("Game time still being tracked. No setting cache yet.")


def main():
    create_and_run_plugin(MinecraftPlugin, sys.argv)


if __name__ == "__main__":
    main()
