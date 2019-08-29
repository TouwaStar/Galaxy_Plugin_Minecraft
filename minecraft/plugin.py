import sys

from galaxy.api.plugin import Plugin, create_and_run_plugin
from galaxy.api.consts import Platform
from galaxy.api.types import Authentication, Game, LicenseInfo, LicenseType, LocalGame, LocalGameState
from version import __version__


if sys.platform == 'win32':
    import winreg

import webbrowser
import logging as log
import os
import subprocess
from local import get_minecraft_launcher_path


class MinecraftPlugin(Plugin):
    def __init__(self, reader, writer, token):
        super().__init__(Platform.BestBuy, __version__, reader, writer, token)
        self.minecraft_launcher = None
        self.minecraft_uninstall_command = None
        self.minecraft_installation_status = LocalGameState.None_
        self.tick_count = 0

    async def authenticate(self, stored_credentials=None):
        self.store_credentials({'dummy': 'dummy'})
        return Authentication(user_id='Minecraft_ID', user_name='Minecraft Player')

    async def get_owned_games(self):
        return [Game('1', 'Minecraft', None, LicenseInfo(LicenseType.SinglePurchase))]

    async def get_local_games(self):
        self.minecraft_launcher = get_minecraft_launcher_path()
        if self.minecraft_launcher:
            return [LocalGame('1', LocalGameState.Installed)]


    async def install_game(self, game_id):
        if sys.platform == 'win32':
            webbrowser.open("https://launcher.mojang.com/download/MinecraftInstaller.msi")
        else:
            webbrowser.open("https://launcher.mojang.com/download/Minecraft.dmg")

    async def launch_game(self, game_id):
        if sys.platform == 'win32':
            cmd = f'"{self.minecraft_launcher}"'
        else:
            cmd = f'open "{self.minecraft_launcher}"'
        log.info(f"Launching minecraft by command {cmd}")
        subprocess.Popen(cmd)

    async def uninstall_game(self, game_id):
        if sys.platform == 'win32':
            subprocess.Popen(f'start {self.minecraft_uninstall_command}')
        else:
            subprocess.Popen(f'open {self.minecraft_uninstall_command}')
        pass

    def tick(self):
        potential_path = get_minecraft_launcher_path()
        if potential_path and not self.minecraft_launcher:
            self.update_local_game_status(LocalGame('1', LocalGameState.Installed))
        elif not potential_path and self.minecraft_launcher:
            self.minecraft_launcher = None
            self.update_local_game_status(LocalGame('1', LocalGameState.None_))



    def shutdown(self):
        # todo
        pass


def main():
    create_and_run_plugin(MinecraftPlugin, sys.argv)


if __name__ == "__main__":
    main()
