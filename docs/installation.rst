安装与环境
==========

iamai 使用 ``uv`` 管理 Python 环境，并通过 ``maturin`` 构建 Rust 扩展。
这意味着开发环境需要同时具备 Python 和 Rust 工具链。

本地开发
--------

在仓库根目录执行：

.. code-block:: bash

   uv sync

这会安装运行时依赖、开发依赖，并构建可编辑安装的 ``iamai`` 包。

验证安装
--------

.. code-block:: bash

   uv run python -m iamai --config examples/echo-runtime/config.terminal.toml config-check

如果输出 ``ok`` 和插件列表，说明 Python 包、Rust 扩展和配置装配都已经可用。

文档环境
--------

文档依赖在独立的 ``docs`` 依赖组里：

.. code-block:: bash

   uv sync --group docs
   uv run sphinx-build -b html docs docs/_build/html

CI 中会使用 ``-W --keep-going`` 构建文档。任何 Sphinx warning 都会让文档任务失败。

常见问题
--------

``ModuleNotFoundError: iamai._core``
   Rust 扩展没有构建或当前 Python 环境没有安装项目。重新执行 ``uv sync``。

``config-check`` 找不到插件
   检查 ``plugins``、``plugin_dirs`` 和 ``python_paths``。默认情况下路径必须位于配置根目录内。

``uv`` 缓存目录没有权限
   在受限环境中可以临时设置 ``UV_CACHE_DIR=/tmp/uv-cache``。
