# MIT License
# Copyright (c) 2016 https://github.com/sndnv
# See the project's LICENSE file for the full text

import signal
from cadb.Core import interrupt_handler, main

if __name__ == '__main__':
    signal.signal(signal.SIGINT, interrupt_handler)
    main()
