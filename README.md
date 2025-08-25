# RetroHiscores

This is a port of the [MAME hiscore plugin](https://github.com/borgar/mame-hiscores) for RetroArch and BizHawk.

It allows saving and restoring hiscores for the games listed in the [datfile](https://github.com/eadmaster/RetroHiscores/blob/master/console_hiscore.dat).

## How to use

### BizHawk

1. Install a recent version of [BizHawk](https://github.com/TASEmulators/BizHawk)
2. copy `RetroHiscores.lua` to `<BizHawk install path>/Lua`
3. copy `console_hiscore.dat` to `<BizHawk install path>/Lua`
4. load a supported game, an `.hi` file will be created in `<BizHawk install path>/Lua`

### RetroArch

1. Obtain a recent version of RetroArch with [Lua scripting support](https://github.com/eadmaster/RetroArch/tree/lua_scripting)
2. copy `RetroHiscores.lua` to `~/.config/retroarch/system/autostart.lua`
3. copy `console_hiscore.dat` to `~/.config/retroarch/system/`
4. load a supported game, an `.hi` file will be created with the current hiscore

## [FAQs](https://github.com/eadmaster/RetroHiscores/wiki/FAQs)
