// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const lightCodeTheme = require("prism-react-renderer/themes/github");
const darkCodeTheme = require("prism-react-renderer/themes/dracula");

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "IAMAI",
  tagline: "Cross-platform robot framework, mainly used for ML",
  favicon: "img/retro.ico",

  // Set the production url of your site here
  url: "https://iamai.retrofor.space",
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: "/",

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: "retrofor", // Usually your GitHub org/user name.
  projectName: "iamai", // Usually your repo name.

  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",

  // Even if you don't use internalization, you can use this field to set useful
  // metadata like html lang. For example, if your site is Chinese, you may want
  // to replace "en" with "zh-Hans".
//   i18n: {
//     defaultLocale: "en",
//     locales: ["en", "zh-Hans"],
//     localeConfigs: {
//       en: {
//         htmlLang: "en-GB",
//       },
//       // 如果你不需要覆盖默认值，你可以忽略这个语言（比如 zh-Hans）
//       fa: {
//         direction: "rtl",
//       },
//     },
//   },

  presets: [
    [
      "classic",
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve("./sidebars.js"),
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl: "https://github.com/retrofor/iamai/tree/main/website/",
        },
        blog: {
          showReadingTime: true,
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl: "https://github.com/retrofor/iamai/tree/main/website/",
        },
        theme: {
          customCss: require.resolve("./src/css/custom.css"),
        },
      }),
    ],
  ],

  // plugins: ['@docusaurus/theme-live-codeblock'],

  //   themes: ['@docusaurus/theme-live-codeblock'],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      //       liveCodeBlock: {
      //         /**
      //          * 实时效果显示的位置，在编辑器上方还是下方。
      //          * 可为："top" | "bottom"
      //          */
      //         playgroundPosition: 'bottom',
      //       },
      algolia: {
        // Algolia 提供的应用 ID
        appId: "93ADZ3VAOB",

        //  公开 API 密钥：提交它没有危险
        apiKey: "47fa7610cea0b76aa428d0a28d7a5491",

        indexName: "iamai.retrofor.space",

        // 可选：见下文
        contextualSearch: true,

        // 可选：声明哪些域名需要用 window.location 型的导航而不是 history.push。 适用于 Algolia 配置会爬取多个文档站点，而我们想要用 window.location.href 在它们之间跳转时。
        // externalUrlRegex: 'external\\.com|domain\\.com',

        // Optional: Replace parts of the item URLs from Algolia. Useful when using the same search index for multiple deployments using a different baseUrl. You can use regexp or string in the `from` param. For example: localhost:3000 vs myCompany.com/docs
        replaceSearchResultPathname: {
          from: "/docs/", // or as RegExp: /\/docs\//
          to: "/",
        },

        // Optional: Algolia search parameters
        searchParameters: {},

        // Optional: path for search page that enabled by default (`false` to disable it)
        searchPagePath: "search",

        //... other Algolia params
      },

      image: "img/docusaurus-social-card.jpg",
      navbar: {
        title: "retrofor?",
        logo: {
          alt: "logo",
          src: "img/logo.svg",
        },
        items: [
          {
            type: "doc",
            docId: "intro",
            position: "left",
            label: "Tutorial",
          },
          { to: "/blog", label: "Blog", position: "left" },
//           {
//             type: "localeDropdown",
//             position: "right",
//           },
          {
            href: "https://github.com/retrofor/iamai",
            label: "GitHub",
            position: "right",
          },
        ],
      },
      footer: {
        style: "dark",
        links: [
          {
            title: "Docs",
            items: [
              {
                label: "Tutorial",
                to: "/docs/intro",
              },
            ],
          },
          {
            title: "Community",
            items: [
              {
                label: "Discord",
                href: "https://discordapp.com/invite/retrofor",
              },
              {
                label: "Twitter",
                href: "https://twitter.com/HsiangNianian",
              },
            ],
          },
          {
            title: "More",
            items: [
              {
                label: "Blog",
                to: "/blog",
              },
              {
                label: "Organization",
                href: "https://github.com/retrofor",
              },
            ],
          },
        ],
        copyright: `Copyright © 2022-${new Date().getFullYear()} , retrofor.`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
      },
    }),
};

module.exports = config;
