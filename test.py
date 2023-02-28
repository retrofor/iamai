d = \
{
    "commits": [
    {
      "id": "0b319200ed1f59378cc9a044537a61513dd9ccf7",
      "tree_id": "78df50b6bae2e33e6370227fccae9fbf2e5f8fc6",
      "distinct": True,
      "message": "✨baka",
      "timestamp": "2023-03-01T01:09:28+08:00",
      "url": "https://github.com/retrofor/iamai/commit/0b319200ed1f59378cc9a044537a61513dd9ccf7",
      "author": {
        "name": "简律纯",
        "email": "hsiangnianian@outlook.com",
        "username": "HsiangNianian"
      },
      "committer": {
        "name": "简律纯",
        "email": "hsiangnianian@outlook.com",
        "username": "HsiangNianian"
      },
      "added": [

      ],
      "removed": [

      ],
      "modified": [
        "test/config.toml"
      ]
    },
    {
      "id": "9700b7507c0f2a0bca65c0bdbfe9036adf415321",
      "tree_id": "59633f2d4fd4b00ff90d52122d2884c2b99c0e12",
      "distinct": True,
      "message": "Merge branch 'main' of https://github.com/retrofor/iamai",
      "timestamp": "2023-03-01T01:09:32+08:00",
      "url": "https://github.com/retrofor/iamai/commit/9700b7507c0f2a0bca65c0bdbfe9036adf415321",
      "author": {
        "name": "简律纯",
        "email": "hsiangnianian@outlook.com",
        "username": "HsiangNianian"
      },
      "committer": {
        "name": "简律纯",
        "email": "hsiangnianian@outlook.com",
        "username": "HsiangNianian"
      },
      "added": [

      ],
      "removed": [

      ],
      "modified": [
        "README.md"
      ]
    }
  ]
}

print('\n--------\n'.join([commit['message'] for commit in d["commits"]]))