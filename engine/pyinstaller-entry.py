import multiprocessing

from engine.cli import main

# Required for ProcessPoolExecutor in a frozen Windows executable.
multiprocessing.freeze_support()
raise SystemExit(main())
