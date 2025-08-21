#!/bin/bash

THIS_SCRIPT_DIR=$(dirname $(readlink -fn $0))

export HISCORE_DAT_PATH="$THIS_SCRIPT_DIR/console_hiscore.dat"
#export HISCORE_PATH="/r"

cd "$THIS_SCRIPT_DIR/tools"

python3 retroarch_hiscore_companion.py "$@"
