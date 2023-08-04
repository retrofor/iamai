const withNextra = require("nextra")({
  theme: 'nextra-theme-docs',
  themeConfig: './theme.config.js',
  latex: true,
  staticImage: true,
  flexsearch: {
    codeblocks: true
  },
  defaultShowCopyCode: true,
});

module.exports = withNextra({
  i18n: {
    locales: ["en-US", "zh-CN"],
    defaultLocale: "en-US",
  },
  reactStrictMode: true,
  webpack: (config) => {
    config.module.rules.push({
      test: /\.(js|jsx|ts|tsx)$/,
      use: {
        loader: 'babel-loader',
        options: {
          presets: ['@babel/preset-env', '@babel/preset-react'],
        },
      },
    });
    return config;
  },
})

