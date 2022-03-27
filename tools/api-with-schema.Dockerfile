FROM dandiarchive/dandiarchive-api
COPY . /opt/dandischema/
RUN cd /opt/dandischema && pip install -e .[dev]
