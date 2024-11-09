from sys import exit as sys_exit
from sys import stderr

from . import main

try:
    main()
except KeyboardInterrupt:
    print("Cancelled with Ctrl+C", file=stderr)
    sys_exit(1)
