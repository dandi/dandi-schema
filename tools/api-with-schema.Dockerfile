FROM dandiarchive/dandiarchive-api
COPY . /opt/dandischema/
RUN uv pip install -e /opt/dandischema[dev]
