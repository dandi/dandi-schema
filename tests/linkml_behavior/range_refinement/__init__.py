# Marks this LinkML-behavior topic directory as a package so that its
# module basenames (`_cases`, `test_validate`, ...) stay distinct from the
# identically named modules in sibling topic directories. Without it, both
# pytest's default "prepend" import mode and mypy resolve those files to the
# same top-level module name and refuse to collect the second one.
