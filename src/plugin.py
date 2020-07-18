import sys, asyncio, logging, urllib, os, json
from galaxy.api.plugin import (
    Plugin,
    LocalGame,
    Authentication,
    Game,
    create_and_run_plugin,
    NextStep,
)
from galaxy.api.consts import LocalGameState, LicenseType, OSCompatibility
from galaxy.api.types import LicenseInfo

from local import WindowsLocalClient, MacLocalClient
from consts import (
    GameID,
    MINECRAFT_DUNGEONS_INSTALL_URL,
    MINECRAFT_MAC_INSTALL_URL,
    MINECRAFT_WIN_INSTALL_URL,
    GAME_NAMES,
)
import more_galaxy_utils as utils

log = logging.getLogger(__name__)


class MinecraftPlugin(Plugin):
    def __init__(self, reader, writer, token):
        super().__init__(utils.manifest.platform, utils.manifest.version, reader, writer, token)
        self.local_client = WindowsLocalClient() if utils.is_windows else MacLocalClient()
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
                "start_uri": os.path.join(utils.dirname, "page", "index.html"),
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
            url = MINECRAFT_WIN_INSTALL_URL if utils.is_windows else MINECRAFT_MAC_INSTALL_URL
        elif game_id == GameID.MinecraftDungeons:
            url = MINECRAFT_DUNGEONS_INSTALL_URL
        else:
            log.warning(f"Uknown game_id to install: {game_id}")
            return
        installer_path = utils.download(url)
        if installer_path is None:
            return
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
                self.game_time_tracker.start_tracking_game(game_id)
                self.status[game_id] = LocalGameState.Installed | LocalGameState.Running
                self.update_local_game_status(LocalGame(game_id, self.status[game_id]))
            elif (
                not self.local_client.is_game_still_running(game_id)
                and pth is not None
                and self.status[game_id] != LocalGameState.Installed
            ):
                if self.game_time_tracker.is_game_being_tracked(game_id):
                    self.game_time_tracker.stop_tracking_game(game_id)
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

    async def get_game_time(self, game_id, context):
        return self.game_time_tracker.get_tracked_time(game_id)

    def handshake_complete(self):
        self.game_time_tracker = utils.BetterTimeTracker(self)

    async def shutdown(self):
        self.game_time_tracker.shutdown()
        await super().shutdown()

    def game_times_import_complete(self):
        if not self.game_time_tracker.update_cache():
            log.debug("Game time still being tracked. No setting cache yet.")


def main():
    create_and_run_plugin(MinecraftPlugin, sys.argv)


if __name__ == "__main__":
    main()
