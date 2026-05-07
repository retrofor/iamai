文档国际化与版本切换
====================

iamai 文档使用 Sphinx 自带 gettext/i18n 能力生成翻译文件，并使用内置
``iamai_i18n_versions`` 扩展在左侧目录栏渲染版本与语言切换器。

维护翻译
--------

默认语言是 ``zh_CN``。翻译文件放在 ``docs/locales`` 下。典型流程：

.. code-block:: console

   uv run --group docs sphinx-build -b gettext docs docs/_build/gettext
   uv run --group docs sphinx-intl update -p docs/_build/gettext -l en
   uv run --group docs sphinx-build -D language=en -b html docs docs/_build/html/en

如果本地没有 ``sphinx-intl``，可以临时运行 ``uv add --group docs sphinx-intl``，或者只使用
Sphinx gettext 输出交给翻译平台处理。

配置切换器
----------

切换器的配置位于 ``docs/conf.py``：

.. code-block:: python

   iamai_docs_current_version = "dev"
   iamai_docs_current_language = "zh_CN"
   iamai_docs_versions = [
       {"name": "dev", "label": "Development", "url": "#", "current": True},
       {"name": "latest", "label": "Latest", "url": "/latest/zh_CN/"},
       {"name": "0.1", "label": "0.1", "url": "/0.1/zh_CN/"},
   ]
   iamai_docs_languages = [
       {"name": "zh_CN", "label": "中文", "url": "#", "current": True},
       {"name": "en", "label": "English", "url": "/dev/en/"},
   ]

``url`` 可以是 ``#``、相对路径、站点根路径或完整 ``http(s)`` URL。部署到 GitHub Pages 时，
推荐把不同版本和语言构建到稳定目录，例如 ``/dev/zh_CN/``、``/dev/en/``、``/latest/zh_CN/``。

扩展输出
--------

构建完成后，扩展会写入 ``_static/iamai-docs-switcher-config.js``，并加载：

- ``_static/iamai-docs-switcher.js``
- ``_static/iamai-docs-switcher.css``

这三个文件共同渲染左侧目录栏里的切换按钮。它是纯静态实现，不需要后端服务。
