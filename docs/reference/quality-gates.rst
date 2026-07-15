质量门禁
========

仓库内置的 CI 会执行以下检查：

.. code-block:: bash

   uv run ruff check .
   uv run pytest
   cargo test --no-default-features
   bash scripts/check_example_configs.sh
   uv run sphinx-build -W --keep-going -b html docs docs/_build/html

本地建议
--------

提交前至少跑：

.. code-block:: bash

   uv run ruff check .
   uv run pytest
   bash scripts/check_example_configs.sh

如果改了文档或 public API，再跑：

.. code-block:: bash

   uv run sphinx-build -W --keep-going -b html docs docs/_build/html
