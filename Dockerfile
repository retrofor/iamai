FROM python:3.10

LABEL maintainer="HsiangNianian <i@jyunko.cn>"
LABEL org.opencontainers.image.description "A simple iamai examples with python 3.10"

RUN apt-get update && \
    apt-get install -y curl && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    export PATH="$HOME/.cargo/bin:$PATH"

WORKDIR /app
COPY . .

RUN python3 -m venv /.venv
RUN /.venv/bin/python -m pip install --upgrade pip && \
    /.venv/bin/python -m pip install pdm maturin
RUN /.venv/bin/python -m pdm sync
RUN /.venv/bin/python -m pdm install -dG dev

CMD ["/.venv/bin/python", "-m", "pdm", "run", "iamai", "version"]