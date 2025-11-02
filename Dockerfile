FROM python:3.11

LABEL maintainer="HsiangNianian <i@jyunko.cn>"

RUN apt-get update && \
    apt-get install -y curl && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

ENV PATH="/root/.cargo/bin:${PATH}"

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.cargo/bin:/root/.local/bin:${PATH}"

WORKDIR /app
COPY . .

RUN python3 -m venv /.venv
RUN /.venv/bin/python -m pip install --upgrade pip && \
    /.venv/bin/python -m pip install pdm maturin
RUN uv sync --all-groups

CMD ["uv", "run", "iamai", "version"]