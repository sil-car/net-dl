import logging
import sys

# Set logging output level.
if '-v' in sys.argv:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=99)
