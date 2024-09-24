FROM rust:latest

USER root

RUN apt-get update && \
    apt-get install -y python3-full

WORKDIR /app
COPY . .

RUN python3 -m venv /.venv
RUN /.venv/bin/python -m pip install pdm maturin
RUN /.venv/bin/python -m pdm sync
RUN /.venv/bin/python -m pdm install -dG dev

CMD ["pdm", "run", "iamai", "version"]