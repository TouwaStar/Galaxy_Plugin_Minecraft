
import sys
if sys.platform == 'win32':
    import winreg

from consts import MINECRAFT_REGISTRY_PATH, MINECRAFT_REGISTRY_PATH_INSTALL_LOCATION_KEY, WINDOWS_UNINSTALL_LOCATION

import logging as log
import os
import psutil
import asyncio

class LocalClient():
    def __init__(self):
        self.running_process = None

    async def get_size_at_path(self, start_path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                await asyncio.sleep(0)
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)

        return total_size

    def get_minecraft_launcher_path(self):
        if sys.platform == 'win32':
            install_path = self.get_minecraft_folder_path()
            potential_path = os.path.join(install_path, 'MinecraftLauncher.exe')
            if os.path.exists(potential_path):
                return potential_path
        else:
            return self.get_minecraft_folder_path()

    def get_minecraft_folder_path(self):
        if sys.platform == 'win32':
            try:
                reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                with winreg.OpenKey(reg, MINECRAFT_REGISTRY_PATH) as key:
                    install_path = winreg.QueryValueEx(key, MINECRAFT_REGISTRY_PATH_INSTALL_LOCATION_KEY)[0]
            except OSError:
                return None
            if os.path.exists(install_path):
                return install_path
        else:
            potential_path = "/Applications/Minecraft.app"
            if os.path.exists(potential_path):
                return potential_path

    def find_minecraft_uninstall_command(self):
        if sys.platform == 'win32':
            reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            with winreg.OpenKey(reg, WINDOWS_UNINSTALL_LOCATION) as key:
                for i in range(0, winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            if winreg.QueryValueEx(subkey,'DisplayName')[0] == 'Minecraft Launcher':
                                return winreg.QueryValueEx(subkey, 'UninstallString')[0]
                    except OSError:
                        continue
        else:
            pass

    def is_minecraft_still_running(self):
        if self.running_process and self.running_process.is_running():
            return True
        elif self.running_process and not self.running_process.is_running():
            self.running_process = None
            return False

    async def was_minecraft_launched(self, process_iter_interval=0.15):
        for process in psutil.process_iter(attrs=['name', 'exe'], ad_value=''):
            await asyncio.sleep(process_iter_interval)
            if process.info['name'].lower() == "minecraftlauncher.exe" or process.info['exe'] == "/Applications/Minecraft.app/Contents/MacOS/launcher":
                log.info(f"Found a running game!")
                self.running_process = process
                return True
        self.running_process = None
        return False
