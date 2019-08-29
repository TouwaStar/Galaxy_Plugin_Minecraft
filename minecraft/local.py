
import sys
if sys.platform == 'win32':
    import winreg

from consts import MINECRAFT_REGISTRY_PATH, MINECRAFT_REGISTRY_PATH_INSTALL_LOCATION_KEY

import logging as log
import os


def get_minecraft_launcher_path():
    if sys.platform == 'win32':
        try:
            reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            with winreg.OpenKey(reg, MINECRAFT_REGISTRY_PATH) as key:
                install_path = winreg.QueryValueEx(key, MINECRAFT_REGISTRY_PATH_INSTALL_LOCATION_KEY)[0]
        except Exception as e:
            log.warning(f"Unable to open Minecraft registry key, probably not installed: {repr(e)}")
            return None
        potential_path = os.path.join(install_path, 'MinecraftLauncher.exe')
        if os.path.exists(potential_path):
            return potential_path
            return [LocalGame('1', LocalGameState.Installed)]
        else:
            log.warning(f"Minecraft entry in registry but not present at install path")
            return None
    else:
        # mac magic
        pass