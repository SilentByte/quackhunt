#
# QUACK HUNT
# Copyright (c) 2023 SilentByte <https://silentbyte.com/>
#

import sys

from quackhunt import game
from quackhunt.detector import calibration_tool_main

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--calibrate':
        calibration_tool_main()
    else:
        game.run()
