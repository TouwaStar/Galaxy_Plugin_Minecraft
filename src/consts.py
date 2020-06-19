import sys
if sys.platform == 'win32':
    import winreg

REGISTRY_START_PATHS = [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]
MINECRAFT_REGISTRY_PATHS = ["SOFTWARE\\Mojang\\InstalledProducts\\Minecraft Launcher", "SOFTWARE\\WOW6432Node\\Mojang\\InstalledProducts\\Minecraft Launcher"]
MINECRAFT_REGISTRY_PATH_INSTALL_LOCATION_KEY = "InstallLocation"
WINDOWS_UNINSTALL_LOCATION = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"


