# GOG Galaxy Minecraft Integration

An Minecraft integration for GOG Galaxy 2.0. Installable via GOG Galaxy (see GIF below).

![example](example.gif)

## FAQ

_How to change what games I own (owned games selection)?_ Just disconnect and reconnect. The play time should be kept. If there is an issue please submit an issue.

## Todo

- [ ] Finish [INSTALL_MULTIMC.md](INSTALL_MULTIMC.md)
- [ ] Refactor local.py (see [these comments in local.py](https://github.com/FriendsOfGalaxy/galaxy-integration-minecraft/pull/8/files#diff-17a1a4cd0d3d33d01fc12d27cd7a4d4c))
- [ ] Reduce overwhelming information on [`page2`](src/page/page2.html) or split it into multiple pages. (see [this comment](https://github.com/TouwaStar/Galaxy_Plugin_Minecraft/pull/10#discussion_r486885489))
- [ ] Clean up the logging
- [ ] Add better commenting/documentation of code
- [ ] Add feature to fetch ownership + username from Mojang API. (see [this comment](https://github.com/FriendsOfGalaxy/galaxy-integration-minecraft/pull/8#discussion_r482571642))
- [ ] Add Minecraft Education edition support

Note: _This list is in no particular order._

## Credits

- Minecraft Dungeons and MultiMC support by [urwrstkn8mare](https://github.com/urwrstkn8mare).
- Build script ([build.py](build.py)) by [urwrstkn8mare](https://github.com/urwrstkn8mare). ([Source](https://gist.github.com/urwrstkn8mare/78d8377562d8719f3bd1f72f9c4e7516))
- `double_click_effect` decorator ([decorators.py](src/decorators.py)) by [UncleGoogle](https://github.com/UncleGoogle). ([Source](https://github.com/UncleGoogle/galaxy-integration-humblebundle/blob/b11918aefac05b904964a8d5330ee1547f11793c/src/utils/decorators.py) - a little modified)
- [style.css](src/page/css/style.css), [fonts](src/page/fonts/), [icon-error.svg](src/page/img/icon-error.svg) by [FriendsOfGalaxy](https://github.com/FriendsOfGalaxy). ([Source](https://github.com/FriendsOfGalaxy/galaxy-integration-steam/commit/ddc594dee637eabda2743370f17efbe4d1dad1bc))
- Info icon ([icon-info.svg](src/page/img/icon-info.svg)) made by [Freepik](https://www.flaticon.com/authors/freepik) from [www.flaticon.com](http://www.flaticon.com/). ([Source](https://www.flaticon.com/free-icon/information-button_1176) - changed colour and made smaller)
- Uses [imgCheckbox](https://jcuenod.github.io/imgCheckbox/) by [jcuenod](https://github.com/jcuenod)
- Uses [jQuery](https://jquery.com/)
- Uses [galaxyutils](https://pypi.org/project/galaxyutils/) by [tylerbrawl](https://github.com/tylerbrawl) and other python packages. Look at [requirements.txt](requirements.txt) for other packages used by this integration.

## Development

First install development dependencies with: `pip install -r requirements/dev.txt`.

Then run:

- `inv pack` to build releases.
- `inv install` to install integration to local GOG Galaxy.
- `inv hotfix` to just overwrite the python files in the install directory.
