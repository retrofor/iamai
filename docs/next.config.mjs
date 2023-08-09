import nextra from 'nextra'

const withNextra = nextra({
  theme: 'nextra-theme-docs',
  themeConfig: './theme.config.tsx',
  latex: true,
  flexsearch: {
    codeblocks: true
  },
  defaultShowCopyCode: true
})

export default withNextra({
  i18n: {
    locales: ["en-US", "zh-CN"],
    defaultLocale: "zh-CN",
  },
  reactStrictMode: true,
  eslint: {
    // Eslint behaves weirdly in this monorepo.
    ignoreDuringBuilds: true
  },
  redirects: () => [
    {
      source: '/docs',
      destination: '/docs/index',
      permanent: true
    },
    {
      source: '/docs/:slug(typescript|latex|tailwind-css|mermaid)',
      destination: '/docs/:slug',
      permanent: true
    },
  ],
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
