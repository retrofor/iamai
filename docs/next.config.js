const withNextra = nextra({
  theme: 'nextra-theme-docs',
  themeConfig: './theme.config.js',
  latex: true,
  staticImage: true,
  flexsearch: {
    codeblocks: true
  },
  defaultShowCopyCode: true,
})

module.exports = withNextra({
  i18n: {
    locales: ["en-US", "zh-CN", "es-ES", "fr-FR", "pt-BR", "ja", "ko", "ru"],
    defaultLocale: "en-US",
  },
  reactStrictMode: true,
  eslint: {
    // Eslint behaves weirdly in this monorepo.
    ignoreDuringBuilds: true
  },
  webpack(config) {
    const allowedSvgRegex = /components\/icons\/.+\.svg$/

    const fileLoaderRule = config.module.rules.find(rule =>
      rule.test?.test('.svg')
    )
    fileLoaderRule.exclude = allowedSvgRegex

    config.module.rules.push({
      test: allowedSvgRegex,
      use: ['@svgr/webpack']
    })
    return config
  }
})
