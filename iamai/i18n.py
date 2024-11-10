import os
import polib
import gettext
import subprocess


from iamai.const import __version__
from typing import List
from gettext import GNUTranslations

localedir = os.path.join(os.path.dirname(__file__), "locale")


def setup_gettext(
    domain: str = os.path.basename(__file__).strip(".py"),
    localedir: str = localedir,
    languages: List[str] = ["en"],
) -> GNUTranslations:
    """Setup gettext

    Args:
        domain (str, optional): Defaults to `os.path.basename(__file__).strip(".py")`.
        localedir (str, optional): Defaults to `localedir`.
        languages (List[str], optional): Defaults to `["en"]`.

    Returns:
        GNUTranslations: The translation object
    """
    try:
        # Try to bind the specified domain
        compile_mo_files(localedir, domain)
        translation = gettext.translation(domain, localedir, languages=languages)
    except FileNotFoundError:
        # Fallback to the default domain 'messages' if the specified domain is not found
        _domain = "messages"
        compile_mo_files(localedir, _domain)
        translation = gettext.translation(
            _domain, localedir, languages=languages, fallback=True
        )

    # Install the translation object globally
    translation.install()
    return translation.gettext


def compile_mo_files(localedir: str, domain: str) -> None:
    """Compile .po files to .mo files

    Args:
        localedir (str): locale directory
        domain (str): locale domain
    """
    for lang in os.listdir(localedir):
        po_path = os.path.join(localedir, lang, "LC_MESSAGES", f"{domain}.po")
        mo_path = os.path.join(localedir, lang, "LC_MESSAGES", f"{domain}.mo")

        if os.path.exists(po_path):
            # Compile if .mo file doesn't exist or is older than the .po file
            if not os.path.exists(mo_path) or os.path.getmtime(
                po_path
            ) > os.path.getmtime(mo_path):
                po = polib.pofile(po_path)
                po.save_as_mofile(mo_path)


class TranslationManager:
    def __init__(self, src_dir="iamai", locale_dir="locale", pot_file="i18n.pot"):
        self.src_dir = src_dir
        self.locale_dir = locale_dir
        self.pot_file = pot_file

    def generate_pot(self):
        py_files = self._find_python_files()
        pot_path = os.path.join(self.src_dir, self.locale_dir, self.pot_file)
        os.makedirs(os.path.dirname(pot_path), exist_ok=True)
        print("Generating POT file...")
        subprocess.run(
            ["xgettext", "-o", pot_path, "--language=Python", "--keyword=_"] + py_files
        )

    def generate_po(self, languages=None):
        if languages is None:
            languages = ["zh"]
        self.generate_pot()
        for lang in languages:
            po_dir = os.path.join(self.src_dir, self.locale_dir, lang, "LC_MESSAGES")
            po_file = os.path.join(po_dir, "i18n.po")
            os.makedirs(po_dir, exist_ok=True)
            if not os.path.isfile(po_file):
                print(f"Generating PO file for language {lang}...")
                subprocess.run(
                    [
                        "msginit",
                        "--locale",
                        lang,
                        "--input",
                        os.path.join(self.src_dir, self.locale_dir, self.pot_file),
                        "--output-file",
                        po_file,
                        "--no-translator",
                    ]
                )
                self._set_utf8_encoding(po_file)
            else:
                print(
                    f"PO file for language {lang} already exists, skipping generation."
                )

    def update_po(self):
        self.generate_pot()
        po_files = self._find_po_files()
        for po_file in po_files:
            print(f"Updating {po_file}...")
            subprocess.run(
                [
                    "msgmerge",
                    "--update",
                    po_file,
                    os.path.join(self.src_dir, self.locale_dir, self.pot_file),
                ]
            )

    def compile_mo(self):
        po_files = self._find_po_files()
        for po_file in po_files:
            mo_file = po_file.replace(".po", ".mo")
            print(f"Compiling {po_file} to {mo_file}...")
            subprocess.run(["msgfmt", "-o", mo_file, po_file])

    def clean(self):
        print("Cleaning up translation files...")
        pot_path = os.path.join(self.src_dir, self.locale_dir, self.pot_file)
        if os.path.exists(pot_path):
            os.remove(pot_path)
        po_files = self._find_po_files()
        for po_file in po_files:
            os.remove(po_file)

    def _find_python_files(self):
        return [
            os.path.join(dp, f)
            for dp, dn, filenames in os.walk(self.src_dir)
            for f in filenames
            if f.endswith(".py")
        ]

    def _find_po_files(self):
        return [
            os.path.join(dp, f)
            for dp, dn, filenames in os.walk(self.src_dir)
            for f in filenames
            if f == "i18n.po"
        ]

    def _set_utf8_encoding(self, po_file):
        with open(po_file, "r+", encoding="utf-8") as file:
            content = file.read()
            content = content.replace("charset=ASCII", "charset=UTF-8")
            file.seek(0)
            file.write(content)
            file.truncate()


if __name__ == "__main__":
    _ = setup_gettext(languages=["zh"])
    print(_("Version: {version}").format(version=__version__))
    manager = TranslationManager()
    manager.generate_po(languages=["fr", "es"])
    manager.update_po()
    manager.compile_mo()
    manager.clean()
