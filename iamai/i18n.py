import os
import polib
import gettext
from typing import Set
from gettext import GNUTranslations

localedir = os.path.join(os.path.dirname(__file__), "locale")

def setup_gettext(
    domain: str = os.path.basename(__file__).strip(".py"),
    localedir: str = localedir,
    languages: Set[str] = {"en"},
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
        translation = gettext.translation(domain, localedir, languages=languages)
        compile_mo_files(localedir, domain)
        print("translation found.")
    except FileNotFoundError:
        # Fallback to the default domain 'messages' if the specified domain is not found
        _domain = "messages"
        translation = gettext.translation(
            _domain, localedir, languages=languages, fallback=True
        )
        compile_mo_files(localedir, _domain)
        print("translation not found, fallback to default domain 'messages'")

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
        print(lang, mo_path, po_path)
        if os.path.exists(po_path):
            # Compile if .mo file doesn't exist or is older than the .po file
            if not os.path.exists(mo_path) or os.path.getmtime(
                po_path
            ) > os.path.getmtime(mo_path):
                po = polib.pofile(po_path)
                po.save_as_mofile(mo_path)
                print(f"Compiled {po_path} to {mo_path}")


if __name__ == "__main__":
    _ = setup_gettext(domain="1", languages={"zh"})
    print(_("hello {name}").format(name="baka"))
