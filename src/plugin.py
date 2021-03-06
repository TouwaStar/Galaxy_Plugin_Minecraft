import sys, asyncio, logging, urllib, os, json, pickle, webbrowser
from galaxy.api.plugin import (
    Plugin,
    LocalGame,
    Authentication,
    Game,
    create_and_run_plugin,
    GameTime,
)
from galaxy.api.consts import LocalGameState, LicenseType, OSCompatibility, Platform
from galaxy.api.types import LicenseInfo
from galaxy.api.errors import InvalidCredentials

from local import WindowsLocalClient, MacLocalClient
from consts import (
    GameID,
    MINECRAFT_DUNGEONS_INSTALL_URL,
    MINECRAFT_MAC_INSTALL_URL,
    MINECRAFT_WIN_INSTALL_URL,
    GAME_NAMES,
    IS_WINDOWS,
    INSTALLED_FOLDER_PATH,
    GAMES,
)
from utils import misc, time_tracker
from utils.decorators import double_click_effect
import multimc
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
        self.multimc: multimc.MultiMCClient = None

    def _authenticate(self):
        return Authentication("Minecraft_ID", "Minecraft Player")

    async def authenticate(self, stored_credentials=None):
        log.debug(f"stored_credentials: {stored_credentials}")
        if stored_credentials is not None:
            if "dummy" in stored_credentials:
                raise InvalidCredentials

            if misc.IS(["owned", "multimcpath"], IN=stored_credentials):
                self.owned = json.loads(stored_credentials["owned"])
                if stored_credentials["multimcpath"] != "null":
                    self.multimc = multimc.MultiMCClient(stored_credentials["multimcpath"])
                return self._authenticate()
        return misc.get_next_step("Select Owned Games", 715, 725, "page1")

    async def pass_login_credentials(self, step, credentials, cookies):
        def auth():
            self.store_credentials(
                {
                    "owned": json.dumps(self.owned),
                    "multimcpath": "null" if self.multimc is None else self.multimc.path,
                }
            )
            return self._authenticate()

        params = urllib.parse.parse_qs(
            urllib.parse.urlsplit(credentials["end_uri"]).query, keep_blank_values=True
        )
        log.debug(f"Params: {params}")
        if "open" in params:
            webbrowser.open_new(params["open"][0])
        if "install_mc" in params and params["install_mc"][0] == "true":
            await self.install_game(GameID.Minecraft)
        if "next" in params:
            nxt = params["next"][0]
            if nxt == "page2":
                new_params = ""
                if "path" in params:
                    raw_path = params["path"][0]
                    new_params = f"?path={urllib.parse.quote(raw_path)}"
                for game_id in GAMES:
                    if game_id in params and params[game_id][0] == "on":
                        self.owned.append(game_id)
                return misc.get_next_step(
                    "Set your MultiMC path", 505, 505, "page2", params=new_params
                )
            elif nxt == "page3":
                if "path" in params:
                    raw_path = params["path"][0]
                    if raw_path != "":
                        path = os.path.expanduser(os.path.expandvars(os.path.abspath(raw_path)))
                        try:
                            self.multimc = multimc.MultiMCClient(path)
                            return misc.get_next_step(
                                "Finished", 410, 355, "page3", params="?multimc=true"
                            )
                        except multimc.PathNotExectuable:
                            return misc.get_next_step(
                                "Set your MultiMC path",
                                530,
                                505,
                                "page2",
                                params=f"?errored=true&path={urllib.parse.quote(raw_path)}",
                            )
                return misc.get_next_step("Finished", 310, 310, "page3")
            elif nxt == "close":
                return auth()

        log.warning("if you see this, something is wrong")

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

    async def get_local_size(self, game_id: str, context):
        size = await misc.get_size_at_path(
            self.local_client.find_launcher_path(game_id, folder=True)
        )
        if game_id == GameID.Minecraft and self._multimc_enabled():
            if size is None:
                size = 0
            size += await misc.get_size_at_path(self.multimc.folder)
        return size

    async def install_game(self, game_id):
        if game_id == GameID.Minecraft:
            url = MINECRAFT_WIN_INSTALL_URL if IS_WINDOWS else MINECRAFT_MAC_INSTALL_URL
        elif game_id == GameID.MinecraftDungeons:
            url = MINECRAFT_DUNGEONS_INSTALL_URL
        else:
            log.warning(f"Uknown game_id to install: {game_id}")
            return
        installer_path = await misc.download(url)
        log.info(f"Installing {game_id} by launching: {installer_path}")
        misc.open_path(installer_path)

    def _launch_multimc(self):
        self.multimc.launch()

    def _multimc_enabled(self):
        return self.multimc is not None

    @double_click_effect(timeout=0.5, effect="_launch_multimc", if_func="_multimc_enabled")
    async def launch_game(self, game_id):
        pth = self.local_client.find_launcher_path(game_id)
        if game_id == GameID.Minecraft and pth is None and self._multimc_enabled():
            log.info("Launching MultiMC")
            self.multimc.launch()
        else:
            self.local_client.launch(game_id)

    async def uninstall_game(self, game_id):
        log.info(f"Uninstalling {game_id}")
        self.local_client.uninstall(game_id)

    async def _update(self):
        def update(game_id, status: LocalGameState):
            if self.status[game_id] != status:
                self.status[game_id] = status
                self.update_local_game_status(LocalGame(game_id, status))
                log.info(f"Updated {game_id} to {status}")
                return True
            return False

        for game_id in self.owned:
            is_installed = self.local_client.find_launcher_path(game_id) is not None
            if game_id == GameID.Minecraft and self._multimc_enabled() and self.multimc.running():
                update(game_id, LocalGameState.Installed | LocalGameState.Running)
            elif self.local_client.is_game_still_running(game_id):
                if update(game_id, LocalGameState.Installed | LocalGameState.Running):
                    log.info(f"Starting to track {game_id}")
                    self.game_time_tracker.start_tracking_game(game_id)
            elif game_id == GameID.Minecraft and self._multimc_enabled():
                update(game_id, LocalGameState.Installed)
            elif is_installed:
                if update(game_id, LocalGameState.Installed):
                    if game_id in self.game_time_tracker.get_tracking_games():
                        self.game_time_tracker.stop_tracking_game(game_id)
                        log.debug(f"Stopped tracking time for {game_id}")
            else:
                update(game_id, LocalGameState.None_)
        await asyncio.sleep(0)

    def tick(self):
        if self.update_task is None or self.update_task.done():
            self.update_task = self.create_task(self._update(), "Update Task")

    # Time Tracker

    async def get_game_time(self, game_id, context):
        try:
            tracked_time = self.game_time_tracker.get_tracked_time(game_id)
        except time_tracker.GameNotTrackedException:
            tracked_time = GameTime(game_id, 0, None)
        if self._multimc_enabled() and game_id == GameID.Minecraft:
            multimc_time = self.multimc.get_time()
        else:
            multimc_time = GameTime(game_id, 0, None)
        time = tracked_time.time_played + multimc_time.time_played
        lastPlayed = misc.compare(tracked_time.last_played_time, multimc_time.last_played_time)
        log.debug(f"Got game time: {time}")
        return GameTime(game_id, time, lastPlayed)

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
                with open(self.play_time_cache_path, "r") as file:
                    for line in file.readlines():
                        if line[:1] != "#":
                            self.game_time_cache = pickle.loads(bytes.fromhex(line))
                            break
            except FileNotFoundError:
                self.game_time_cache = None
        self.game_time_tracker = time_tracker.TimeTracker(game_time_cache=self.game_time_cache)

    async def shutdown(self):
        for game_id in self.game_time_tracker.get_tracking_games():
            self.game_time_tracker.stop_tracking_game(game_id)
        if self.game_time_cache is not None:
            with open(self.play_time_cache_path, "w+") as file:
                file.write("# DO NOT EDIT THIS FILE\n")
                file.write(self.game_time_tracker.get_time_cache_hex())
                log.info("Wrote to local file cache")
        await super().shutdown()

    def game_times_import_complete(self):
        if len(self.game_time_tracker.get_tracking_games()) > 0:
            log.debug("Game time still being tracked. Not setting cache yet.")
        else:
            self.game_time_cache = self.game_time_tracker.get_time_cache()
            log.debug(f"game_time_cache: {self.game_time_cache}")
            self.persistent_cache["game_time_cache"] = self.game_time_tracker.get_time_cache_hex()
            self.push_cache()


def main():
    create_and_run_plugin(MinecraftPlugin, sys.argv)


if __name__ == "__main__":
    main()
