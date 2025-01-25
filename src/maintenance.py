#!/usr/bin/env python3

"""
Usage:
    ./%(script_name)s (up|down)

Examples:
    # Enter maintenance mode
    ./%(script_name)s up

    # Exit maintenance mode
    ./%(script_name)s down
"""

import logging
import os
import sys
from pathlib import Path

from docopt import docopt

from src.config import MAINTENANCE_FILE

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)


__doc__ %= {
    "script_name": Path(__file__).name,
}


def main(argv: list[str] | None = None):
    if argv is None:
        argv = sys.argv[1:]

    args = docopt(__doc__, argv=argv)
    if args.get("up"):
        if os.path.exists(MAINTENANCE_FILE):
            logger.error("Maintenance mode is already enabled")
        else:
            Path(MAINTENANCE_FILE).touch()
            logger.info("Maintenance mode enabled")
    elif args.get("down"):
        if not os.path.exists(MAINTENANCE_FILE):
            logger.error("Maintenance mode is already disabled")
        else:
            os.remove(MAINTENANCE_FILE)
            logger.info("Maintenance mode disabled")
    else:
        raise NotImplementedError("Invalid option")


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    main()
