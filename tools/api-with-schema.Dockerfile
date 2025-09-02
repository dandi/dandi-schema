FROM dandiarchive/dandiarchive-api
COPY . /opt/dandischema/
RUN cd /opt/dandischema && uv pip install --system -e .[dev]
