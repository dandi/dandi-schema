# Marks the LinkML-behavior test tree as a package so the topic directories
# below it can share helpers via relative imports (`from .._generation import
# ...`). See `_generation.py` for why those helpers are wrapped in per-topic
# fixtures rather than being inherited from a parent `conftest.py`.
