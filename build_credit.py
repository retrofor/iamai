import os
import re
import json
import pathlib

import httpx
from python_graphql_client import GraphqlClient

root = pathlib.Path(__file__).parent.resolve()
client = GraphqlClient(endpoint="https://api.github.com/graphql")

with open(f"{root}/credit.json", "r", encoding="utf-8") as credit_file:
    credit = json.loads(credit_file.read())

TOKEN = os.environ.get("GITHUB_TOKEN", "")


def replace_chunk(content, marker, chunk, inline=False):
    r = re.compile(
        f"<!\-\- {marker} starts \-\->.*<!\-\- {marker} ends \-\->", re.DOTALL
    )
    if not inline:
        chunk = f"\n{chunk}\n"
    chunk = f"<!-- {marker} starts -->{chunk}<!-- {marker} ends -->"
    return r.sub(chunk, content)


def fetch_mlf_denpendices():
    dependencies = credit["MachineLearningFramework"]
    return [
        {
            "name": _["name"],
            "version": _["versionInfo"],
            "license": _["license"],
            "repo": _["repo"],
            "licenseUrl": _["licenseUrl"],
            "description": _["description"],
            "icon": _["icon"],
        }
        for _ in dependencies
    ]


def fetch_cprf_denpendices():
    dependencies = credit["RobotFramework"]
    return [
        {
            "name": _["name"],
            "version": _["versionInfo"],
            "license": _["license"],
            "repo": _["repo"],
            "licenseUrl": _["licenseUrl"],
            "description": _["description"],
            "icon": _["icon"],
        }
        for _ in dependencies
    ]


if __name__ == "__main__":
    readme = root / "README.md"
    readme_contents = readme.open().read()
    # MLF
    MLF = fetch_mlf_denpendices()
    MLF_md = "\n\n".join(
        [
            "[{name}]({repo})({version}) with [{license}]({licenseUrl}). {icon} `{description}`".format(
                **_
            )
            for _ in MLF
        ]
    )
    print()
    print(MLF_md)
    print()
    rewritten = replace_chunk(readme_contents, "MLF", MLF_md)

    # CPRF
    CPRF = fetch_cprf_denpendices()
    CPRF_md = "\n\n".join(
        [
            "[{name}]({repo})({version}) with [{license}]({licenseUrl}). {icon} `{description}`".format(
                **_
            )
            for _ in CPRF
        ]
    )
    print()
    print(CPRF_md)
    print()
    rewritten = replace_chunk(rewritten, "CPRF", CPRF_md)

    readme.open("w").write(rewritten)
