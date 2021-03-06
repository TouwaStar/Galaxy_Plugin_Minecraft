import os, logging

from consts import (
    GameID,
    REGISTRY_START_PATHS,
    SOFTWARE_PATHS,
    GAME_REGISTY_RELATIVE_LOCATIONS,
    REGISTRY_EXE_KEYS,
    WIN_UNINSTALL_RELATIVE_LOCATION,
    IS_WINDOWS,
)
from utils import misc


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
        return self.running_games[game_id] and self.running_games[game_id].poll() is None

    def launch(self, game_id):
        log.info(f"Launching {game_id}")
        self.running_games[game_id] = misc.open_path(self.find_launcher_path(game_id))

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
                                misc.run(winreg.QueryValueEx(subkey, "UninstallString")[0])
                                return
                    except OSError:
                        pass
                winreg.CloseKey(key)


class MacLocalClient(LocalClient):
    def find_launcher_path(self, game_id, *, folder=False):
        if game_id == GameID.Minecraft:
            potential_path = "/Applications/Minecraft.app"
            if os.path.exists(potential_path):
                return super().find_launcher_path(game_id, folder=folder, exe=potential_path)
        return super().find_launcher_path(game_id, folder=folder)

    def uninstall(self, game_id):
        misc.send2trash(self.find_launcher_path(game_id, folder=True))
