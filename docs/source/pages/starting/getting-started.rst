===========
Quick Start
===========

Installation
============

.. tip::
   iamai only supports Python 3.8+ versions.

.. todolist:: 

Install using the Python package manager (pip):

.. code-block:: sh
   :linenos:
   
   pip install iamai


Install the latest development version from GitHub.

.. code-block:: sh
   :linenos:

   git clone https://github.com/retrofor/iamai.git
   cd iamai
   poetry install --no-dev # Recommended


Installing Adapters
-------------------

iamai itself is just a chatbot framework and requires additional installation of adapters for supporting specific protocols. 

You can use pip to install protcol adapters ::

   pip install iamai-adapter-cqhttp
   pip install iamai-adapter-mirai
   pip install iamai-adapter-dingtalk


Alternatively, you can install iamai along with the corresponding adapters at the same time, like this ::

   pip install iamai[all]
   pip install iamai[onebot11]
   pip install iamai[dingtalk]


First Project
-------------

.. todo:: 
   support atleast 5 adapters

This section will guide you to build a simple iamai bot project from scratch.

1. Create and enter a new directory ::

   mkdir iamai-starter && cd iamai-starter

2. Create a `main.py` file and write the following content.

.. code-block:: python3
   :linenos:
   
   from iamai import Bot

   bot = Bot()

   if __name__ == "__main__":
     bot.run()

3. Create a `config.toml` file and write the following content inside that file:

.. code-block:: toml
   :linenos:
   
   [bot]
   plugin_dirs = ["plugins"]
   adapters = ["iamai.adapter.cqhttp"]

4. Create a `plugins` directory ::

   mkdir plugins

5. Try Running `main.py` ::

   python main.py

You should see the following output log ::

   2021-07-24 00:00:00.000 | INFO | iamai.bot:_load_plugins_from_dirs:689 - Loading plugins from dirs "/xxx/plugins"
   2021-07-24 00:00:00.000 | INFO | iamai.bot:_load_adapters:746 - Succeeded to load adapter "Onebot11Adapter" from "iamai.adapter.onebot11"
   2021-07-24 00:00:00.000 | INFO | iamai:run:90 - Running iamai...


Directory Structure
-------------------

iamai recommends the following directory structure:

<FileTree>
  <FileTree.Folder name="plugins (The plugins dir)" defaultOpen>
    <FileTree.File name="xxx.py" />
  </FileTree.Folder>
  <FileTree.File name="config.toml (The configuration file)" />
  <FileTree.File name="main.py" />
</FileTree>

The `main.py` and `config.toml` files are as shown above.

Configuring the Protocol Enpoint
--------------------------------

The above example uses the `iamai.adapter.cqhttp` protocol adapter, which is an adapter for the OneBot v11 protocol (formerly known as the CKYU platform's CQHTTP protocol). It requires a protocol endpoint compatible with the OneBot protocol for communication. Here are some commonly used QQ protocol endpoints that support the OneBot protocol:

- [go-cqhttp](https://github.com/Mrs4s/go-cqhttp)
- [mirai](https://github.com/mamoe/mirai) + [onebot-kotlin](https://github.com/yyuueexxiinngg/onebot-kotlin)
- [oicq](https://github.com/takayama-lily/oicq)

For more information, see the [CQHTTP Protocol Usage Guide](./cqhttp-adapter.md) .

You can also install other protocols adapters or try writing your own protocol adapter.

## Development Tips

When developing with iamai, it is recommended to use an IDE with type checking, such as PyCharm, VSCode, etc. This can help you make full use of iamai's type hints.
