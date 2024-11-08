import gettext

t = gettext.translation("iamai", "/locale")


def _(message):
    return t.gettext(message)


if __name__ == "__main__":
    print(_("hello world"))
