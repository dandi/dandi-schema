FROM python:3.9-slim
# Install system librarires for Python packages:
# * psycopg2
RUN apt-get update && \
    apt-get install --no-install-recommends --yes \
        libpq-dev gcc libc6-dev git && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED 1

WORKDIR /opt/dandischema
COPY . /opt/dandischema/
RUN pip install -e .[dev]

WORKDIR /opt/django
RUN git clone https://github.com/dandi/dandi-api . && pip install -e .[dev]
