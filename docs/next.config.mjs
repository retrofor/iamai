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
      source: '/docs/robot',
      destination: '/docs/robot/index',
      permanent: false
    },
    {
      source: '/docs/robot/:slug(typescript|latex|tailwind-css|mermaid)',
      destination: '/docs/robot/:slug',
      permanent: true
    },
    {
      source: '/docs/ai/:slug(callout|steps|tabs)',
      destination: '/docs/ai/:slug',
      permanent: true
    }
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
