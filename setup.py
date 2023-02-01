import setuptools

with open("README.md", "rb") as fh:
    long_description = fh.read().decode("utf-8")

setuptools.setup(
    name='retrofor_wut',
    version='4.0.2',
    url='https://github.com/retrofor/retrofor_wut',
    license='MIT',
    author='简律纯',
    author_email='HsiangNianian@outlook.com',
    description='Cross-platform robot framework, mainly used for machine learning.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Framework :: AsyncIO",
        "Framework :: Robot Framework",
        "Framework :: Robot Framework :: Library",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Communications :: Chat",
    ],
    python_requires='>=3.8',
    install_requires=['flask','pydantic','loguru','aiohttp','tomli','typing-extensions','pydantic','watchfiles'],
)
