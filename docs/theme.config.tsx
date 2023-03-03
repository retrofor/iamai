import React from 'react'
import { DocsThemeConfig } from 'nextra-theme-docs'

const config: DocsThemeConfig = {
  logo: <span>IamAI</span>,
  project: {
    link: 'https://github.com/retrofor/iamai',
  },
  chat: {
    link: 'https://discord.gg/9vG9352RXS',
  },
  docsRepositoryBase: 'https://github.com/retrofor/iamai-docs/tree/main',
  i18n: [
    { locale: 'en', text: 'English' },
    { locale: 'zh', text: '中文' }
  ],
  footer: {
    text: 'Copyright (c) 2023 retrofor',
  }
}

export default config
