FROM dandiarchive/dandiarchive-api
COPY . /opt/dandischema/
RUN uv pip install -e /opt/dandischema

# The base image's `manage.py` runs via `#!/usr/bin/env -S uv run`, and `uv run`
# syncs `/opt/django/.venv` to `uv.lock` before executing, which would reinstall
# the `dandischema` release pinned by `dandi-archive` over the one installed
# above. That sync must be skipped for this image to run the schema version
# under test; skipping it is safe because the base image's `uv sync` has already
# installed every other dependency.
ENV UV_NO_SYNC=1
