import platform, os

IS_WINDOWS = platform.system().lower() == "windows"

if IS_WINDOWS:
    import winreg
    REGISTRY_START_PATHS = [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]
else:
    REGISTRY_START_PATHS = []

class GameID:
    Minecraft = "mc"
    MinecraftDungeons = "mcd"
    MinecraftEducationEdition = "mcedu"


INSTALLED_FOLDER_PATH = os.path.abspath(
    os.path.expandvars("%localappdata%\\GOG.com\\Galaxy\\plugins\\installed")
    if IS_WINDOWS
    else os.path.expanduser("~/Library/Application Support/GOG.com/Galaxy/plugins/installed")
)

DIRNAME = os.path.abspath(os.path.join(__file__, ".."))

SOFTWARE_PATHS = ["SOFTWARE\\", "SOFTWARE\\WOW6432Node\\"]
mojang_registry_relative_location = "Mojang\\InstalledProducts\\"
GAME_REGISTY_RELATIVE_LOCATIONS = {
    GameID.Minecraft: mojang_registry_relative_location + "Minecraft Launcher",
    GameID.MinecraftDungeons: mojang_registry_relative_location + "Minecraft Dungeons Launcher",
}
REGISTRY_EXE_KEYS = {GameID.Minecraft: "InstallExe", GameID.MinecraftDungeons: "InstallFile"}
WIN_UNINSTALL_RELATIVE_LOCATION = "Microsoft\\Windows\\CurrentVersion\\Uninstall"
MINECRAFT_WIN_INSTALL_URL = "https://launcher.mojang.com/download/MinecraftInstaller.msi"
MINECRAFT_MAC_INSTALL_URL = "https://launcher.mojang.com/download/Minecraft.dmg"
MINECRAFT_DUNGEONS_INSTALL_URL = (
    "https://launcher.mojang.com/download/MinecraftDungeonsInstaller.msi"
)


GAME_NAMES = {GameID.Minecraft: "Minecraft", GameID.MinecraftDungeons: "Minecraft Dungeons"}
