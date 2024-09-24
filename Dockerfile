FROM python:3.9

LABEL maintainer="HsiangNianian <i@jyunko.cn>"

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