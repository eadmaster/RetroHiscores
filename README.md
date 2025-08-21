# RetroHiscores

This is a port of the [MAME hiscore plugin](https://github.com/borgar/mame-hiscores) for RetroArch.

It allows saving and restoring hiscores for games listed in the datfile.

> [!NOTE]
> Only games with [builtin hiscores buffering](https://github.com/eadmaster/RetroHiscores/wiki/FAQs#can-you-track-hiscores-for-all-the-games) are supported currently.


## How to use

1. Obtain a recent version of RetroArch with [Lua scripting support](https://github.com/eadmaster/RetroArch/tree/lua_scripting)
2. copy `RetroHiscores.lua` to `~/.config/retroarch/system/autostart.lua`
3. copy `console_hiscore.dat` to `~/.config/retroarch/system/`
4. load a supported game, and `.hi` file will be created with the current hiscore


