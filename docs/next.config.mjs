import nextra from 'nextra'

const withNextra = nextra({
  theme: 'nextra-theme-docs',
  themeConfig: './theme.config.tsx',
  latex: true,
  flexsearch: {
    codeblocks: true
  },
  defaultShowCopyCode: true,
  i18n: {
    locales: ['en-US', 'zh-CN'],
    defaultLocale: 'en-US',
    domains: [
      {
        // Note: subdomains must be included in the domain value to be matched
        // e.g. www.example.com should be used if that is the expected hostname
        domain: 'iamai.retrofor.space',
        defaultLocale: 'en-US',
      },
      {
        domain: 'iamai.retrofor.zh',
        defaultLocale: 'zh-CN',
      },
    ],
    localeDetection: false,
  },
})

export default withNextra({
  reactStrictMode: true,
  eslint: {
    // Eslint behaves weirdly in this monorepo.
    ignoreDuringBuilds: true
  },
  // webpack(config) {
  //   const allowedSvgRegex = /components\/icons\/.+\.svg$/

  //   const fileLoaderRule = config.module.rules.find(rule =>
  //     rule.test?.test('.svg')
  //   )
  //   fileLoaderRule.exclude = allowedSvgRegex

  //   config.module.rules.push({
  //     test: allowedSvgRegex,
  //     use: ['@svgr/webpack']
  //   })
  //   return config
  // }
})
