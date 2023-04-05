#
# QUACK HUNT
# Copyright (c) 2023 SilentByte <https://silentbyte.com/>
#

import sys
from time import time
from pprint import pformat


def debug_print(object, prefix: str = '', buffer_time=1.0) -> None:
    output = pformat(object)

    if not output:
        return

    now = time()
    if now - debug_print.last_output_time >= buffer_time:
        print(prefix, output, f'({debug_print.duplicate_counter}x)')
        debug_print.last_output_time = now
        debug_print.duplicate_counter = 0

    if debug_print.last_output == output:
        debug_print.duplicate_counter += 1
        return

    if debug_print.duplicate_counter == 0:
        print(prefix, output)
        debug_print.last_output_time = now
        debug_print.last_output = output
        return

    print(prefix, output, f'({debug_print.duplicate_counter}x)')

    debug_print.last_output_time = now
    debug_print.last_output = None
    debug_print.duplicate_counter = 0


debug_print.last_output_time = sys.maxsize
debug_print.last_output = None
debug_print.duplicate_counter = 0
