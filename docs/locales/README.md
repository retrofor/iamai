# iamai documentation locales

Sphinx i18n files live under this directory.

Typical workflow:

```bash
uv run --group docs sphinx-build -b gettext docs docs/_build/gettext
uv run --group docs sphinx-intl update -p docs/_build/gettext -l en
uv run --group docs sphinx-build -D language=en -b html docs docs/_build/html/en
```

If `sphinx-intl` is not installed, add it to the docs dependency group before
running the update command.

The switcher is static and reads its version/language entries from
`iamai_docs_versions` and `iamai_docs_languages` in `docs/conf.py`.
