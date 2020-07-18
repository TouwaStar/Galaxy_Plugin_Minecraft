import os, asyncio, logging

import psutil

from consts import (
    GameID,
    REGISTRY_START_PATHS,
    SOFTWARE_PATHS,
    GAME_REGISTY_RELATIVE_LOCATIONS,
    REGISTRY_EXE_KEYS,
    WIN_UNINSTALL_RELATIVE_LOCATION,
    IS_WINDOWS,
)
import utils


if IS_WINDOWS:
    import winreg

log = logging.getLogger(__name__)


class LocalClient:
    def __init__(self):
        self.running_games = {
            GameID.Minecraft: None,
            GameID.MinecraftDungeons: None,
        }

    def find_launcher_path(self, game_id, *, folder=False, folder_path=None, exe=None) -> str:
        if exe is None and folder_path is not None:
            folder_path = None
        if exe is not None and folder_path is None:
            folder_path = exe
        if exe is not None and folder_path is not None:
            folder_path = os.path.abspath(folder_path)
            exe = os.path.abspath(exe)
        log.debug(f"folder path for {game_id}: {folder_path}")
        log.debug(f"path for {game_id}: {exe}")
        return exe if not folder else folder_path

    def is_game_still_running(self, game_id) -> bool:
        rp = self.running_games[game_id]  # Just an alias
        if rp is not None and rp.is_running():
            return True
        elif rp is not None and not rp.is_running():
            # Can't use rp alias as it won't update the dict.
            self.running_games[game_id] = None
        return False

    async def check_games_launched(self):
        pass

    def uninstall(game_id):
        pass


class WindowsLocalClient(LocalClient):
    def find_launcher_path(self, game_id, folder=False):
        for start_path in REGISTRY_START_PATHS:
            for software_path in SOFTWARE_PATHS:
                reg = winreg.ConnectRegistry(None, start_path)
                try:
                    with winreg.OpenKey(
                        reg, software_path + GAME_REGISTY_RELATIVE_LOCATIONS[game_id]
                    ) as key:
                        directory = winreg.QueryValueEx(key, "InstallLocation")[0]
                        return super().find_launcher_path(
                            game_id,
                            folder=folder,
                            folder_path=directory,
                            exe=os.path.join(
                                directory, winreg.QueryValueEx(key, REGISTRY_EXE_KEYS[game_id])[0]
                            ),
                        )
                except OSError:
                    pass
        return super().find_launcher_path(game_id, folder=folder)

    def uninstall(self, game_id):
        targetDisplayName = None
        if game_id == GameID.Minecraft:
            targetDisplayName = "Minecraft Launcher"
        elif game_id == GameID.MinecraftDungeons:
            targetDisplayName = "Minecraft Dungeons Launcher"
        for start_path in REGISTRY_START_PATHS:
            for software_path in SOFTWARE_PATHS:
                reg = winreg.ConnectRegistry(None, start_path)
                try:
                    key = winreg.OpenKey(reg, software_path + WIN_UNINSTALL_RELATIVE_LOCATION)
                except OSError:
                    continue
                for i in range(0, winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            if winreg.QueryValueEx(subkey, "DisplayName")[0] == targetDisplayName:
                                utils.run(winreg.QueryValueEx(subkey, "UninstallString")[0])
                                return
                    except OSError:
                        pass
                winreg.CloseKey(key)

    async def was_game_launched(self, process_iter_interval=0.15):
        found_mc, found_mcd = False, False
        for p in psutil.process_iter(attrs=["name"], ad_value=""):
            # await asyncio.sleep(process_iter_interval)
            if p.info["name"].lower() == "minecraftlauncher.exe":
                self.running_games[GameID.Minecraft] = p
                found_mc = True
            elif p.info["name"].lower() == "minecraftdungeonslauncher.exe":
                self.running_games[GameID.MinecraftDungeons] = p
                found_mcd = True
            if found_mc and found_mcd:
                return
        if not found_mc:
            self.running_games[GameID.Minecraft] = None
        if not found_mcd:
            self.running_games[GameID.MinecraftDungeons] = None
        await asyncio.sleep(5)


class MacLocalClient(LocalClient):
    def find_launcher_path(self, game_id, *, folder=False):
        if game_id == GameID.Minecraft:
            potential_path = "/Applications/Minecraft.app"
            if os.path.exists(potential_path):
                return super().find_launcher_path(game_id, folder=folder, exe=potential_path)
        return super().find_launcher_path(game_id, folder=folder)

    def uninstall(self, game_id):
        utils.send2trash(self.find_launcher_path(game_id, folder=True))

    async def was_game_launched(self, process_iter_interval=0.15):
        for p in psutil.process_iter(attrs=["exe"], ad_value=""):
            await asyncio.sleep(process_iter_interval)
            if p.info["exe"] == "/Applications/Minecraft.app/Contents/MacOS/launcher":
                self.running_games[GameID.Minecraft] = p
                return
        self.running_games[GameID.Minecraft] = None
        await asyncio.sleep(5)
