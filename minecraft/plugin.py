import sys

from galaxy.api.plugin import Plugin, create_and_run_plugin
from galaxy.api.consts import Platform
from galaxy.api.types import Authentication, Game, LicenseInfo, LicenseType
from version import __version__

if sys.platform == 'win32':
    import winreg

import webbrowser


class MinecraftPlugin(Plugin):
    def __init__(self, reader, writer, token):
        super().__init__(Platform.BestBuy, __version__, reader, writer, token)

    async def authenticate(self, stored_credentials=None):
        return Authentication(user_id='Minecraft_ID', user_name='Minecraft Player')

    async def get_owned_games(self):
        return [Game('1', 'Minecraft', None, LicenseInfo(LicenseType.SinglePurchase))]

    async def get_local_games(self):
        if sys.platform == 'win32':
            #winreg magic
            pass
        else:
            #mac magic
            pass

    async def install_game(self, game_id):
        if sys.platform == 'win32':
            webbrowser.open("https://launcher.mojang.com/download/MinecraftInstaller.msi")
        else:
            webbrowser.open("https://launcher.mojang.com/download/Minecraft.dmg")

    async def launch_game(self, game_id):
        # todo
        pass

    async def uninstall_game(self, game_id):
        # todo
        pass

    def tick(self):
        # todo
        pass

    def shutdown(self):
        # todo
        pass


def main():
    create_and_run_plugin(MinecraftPlugin, sys.argv)


if __name__ == "__main__":
    main()
