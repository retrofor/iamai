import { useRouter } from "next/router";
import { useConfig } from "nextra-theme-docs";
import useLocalesMap from "./components/use_locales_map";
import {
  editTextMap,
  feedbackLinkMap,
  languageMap,
} from "./translation/text";

const logo = (
  <span>
    <svg height="40" viewBox="0 0 64 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <style>
        {
          `.st0 {
				fill: #fff
			}

			.st1 {
				fill: #3d69a8
			}

			.st2 {
				fill: #29993a
			}

			.st3 {
				fill: #8fcce7
			}

			.st4 {
				fill: #6ca0cf
			}

			.st5 {
				fill: #000000
			}

			`
        }
      </style>
      <path d="M3 4v1h1V4h1V3h5v2h2v1h1V5h1V3h-2v1h-1V1H8v1H7V1H4v1H3v1H2v1z" className="st0" />
      <path d="M2 9h1v1h4V8h1V7h2V5H7v1H6v1H5V6H2v1H1v1h1zM9 10v1h1v-1h1V9H9z" className="st0" />
      <path d="M5 14h4v1H5zM14 11v1h-1v1h-2v1h3v-1h1v-3h-1zM14 7h1v1h-1z" className="st1" />
      <path
        d="M1 8V7h1V6h1V5H2V3H1v3H0v5h1v-1zM2 2h1v1H2zM3 1h1v1H3zM4 0h3v1H4zM7 1h1v1H7zM8 0h3v1H8zM11 4h1V3h2V2h-2V1h-1v2zM14 3h1v1h-1zM15 4v4h-2v1h1v1h1V9h1V4zM15 13h1v-3h-1v2zM14 13h1v1h-1zM11 14h3v1h-3zM10 13h1v1h-1zM9 14h1v1H9zM5 15h4v1H5zM4 14h1v1H4zM4 12H2v1h1v1h1v-1zM1 11h1v1H1z"
        className="st5" />
      <path d="M5 6v1h1V6h1V5h3V3H5v1H4v2zM8 7v1H7v2h2V9h2V8h1V5h-2v2zM7 11h2v2H7z" className="st2" />
      <path
        d="M9 11v-1H3V9H2V8H1v2h1v1h2v1h1v1h2v-2zM14 5h-1v1h-1v2h-1v2h-1v1H9v2h1v-1h2v-1h1V8h1V7h1V4h-1zM2 4h1v1H2zM3 5h1v1H3z"
        className="st3" />
      <path d="M1 10h1v1H1zM4 11H2v1h2zM9 13H5v-1H4v2h6v-1zM12 11v1h-2v1h3v-1h1V9h-1v2z" className="st4" />
      <path
        d="M26.35 6.2h-1.11V5h1.11v1.2zm0 7.39h-1.11V7.38h1.11v6.21zM31.92 12.96c-.56.52-1.29.79-2.17.79-.62 0-1.12-.17-1.52-.5s-.6-.76-.6-1.29c0-1.45 1.25-2.18 3.76-2.18h.54c0-.45-.02-.77-.07-.97s-.18-.37-.39-.5-.56-.2-1.03-.2c-.98 0-1.49.35-1.52 1.05h-1.1c.08-1.28.98-1.92 2.68-1.92.8 0 1.42.16 1.86.47s.67.94.67 1.86v4.02h-1.1v-.63zm0-1v-1.38h-.76c-1.6 0-2.4.44-2.4 1.31 0 .32.12.56.35.73s.55.25.95.25c.36 0 .71-.08 1.05-.25s.62-.38.81-.66zM43.06 13.59h-1.11V9.57c0-.52-.07-.88-.22-1.1s-.4-.33-.74-.33c-.54 0-1.06.33-1.58 1v4.45h-1.1V9.57c0-.52-.07-.88-.22-1.1s-.4-.33-.75-.33c-.54 0-1.06.33-1.57 1v4.45h-1.11V7.38h1.11v.79c.52-.62 1.1-.93 1.74-.93.91 0 1.49.38 1.74 1.12.41-.49.77-.8 1.05-.93s.57-.2.85-.2c1.27 0 1.91.76 1.91 2.29v4.07zM48.59 12.96c-.56.52-1.29.79-2.17.79-.62 0-1.12-.17-1.52-.5s-.6-.76-.6-1.29c0-1.45 1.25-2.18 3.76-2.18h.54c0-.45-.02-.77-.07-.97s-.18-.37-.39-.5-.56-.2-1.03-.2c-.98 0-1.49.35-1.52 1.05h-1.1c.08-1.28.98-1.92 2.68-1.92.8 0 1.42.16 1.86.47s.67.94.67 1.86v4.02h-1.1v-.63zm0-1v-1.38h-.76c-1.6 0-2.4.44-2.4 1.31 0 .32.12.56.35.73s.55.25.95.25c.36 0 .71-.08 1.05-.25s.62-.38.81-.66zM52.43 6.2h-1.11V5h1.11v1.2zm0 7.39h-1.11V7.38h1.11v6.21z"
        fill="currentColor" />

    </svg> <style jsx>{`
      span {
        padding: 0.5rem 0.5rem 0.5rem 0;
        mask-image: linear-gradient(
          60deg,
          black 25%,
          rgba(0, 0, 0, 0.2) 50%,
          black 75%
        );
        mask-size: 400%;
        mask-position: 0%;
      }
      span:hover {
        mask-position: 100%;
        transition:
          mask-position 1s ease,
          -webkit-mask-position 1s ease;
      }
    `}</style>
  </span>
)

/** @type {import('nextra-theme-docs').DocsThemeConfig} */
const themeConfig = {
  project: {
    link: 'https://github.com/retrofor/iamai'
  },
  docsRepositoryBase: 'https://github.com/retrofor/iamai/tree/master/docs',
  useNextSeoProps() {
    const { asPath } = useRouter()
    if (asPath !== '/') {
      return {
        titleTemplate: '%s – iamai'
      }
    }
  },
  logo,
  head: function useHead() {
    const { title } = useConfig()
    const { route } = useRouter()
    const socialCard =
      route === '/' || !title
        ? 'https://iamai.retrofor.space/og.jpeg'
        : `https://iamai.retrofor.space/api/og?title=${title}`

    return (
      <>
        <meta name="msapplication-TileColor" content="#fff" />
        <meta name="theme-color" content="#fff" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <meta httpEquiv="Content-Language" content="en" />
        <meta
          name="description"
          content="Make a bridge between AI and robot."
        />
        <meta
          name="og:description"
          content="Make a bridge between AI and robot."
        />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:image" content={socialCard} />
        <meta name="twitter:site:domain" content="iamai.retrofor.space" />
        <meta name="twitter:url" content="https://iamai.retrofor.space" />
        <meta
          name="og:title"
          content={title ? title + ' – iamai' : 'iamai'}
        />
        <meta name="og:image" content={socialCard} />
        <meta name="apple-mobile-web-app-title" content="iamai" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="icon" href="/favicon.png" type="image/png" />
        <link
          rel="icon"
          href="/favicon-dark.svg"
          type="image/svg+xml"
          media="(prefers-color-scheme: dark)"
        />
        <link
          rel="icon"
          href="/favicon-dark.png"
          type="image/png"
          media="(prefers-color-scheme: dark)"
        />
      </>
    )
  },
  banner: {
    key: '3.0-release',
    text: (
      <a href="https://iamai.retrofor.space/blog/iamai-v3" target="_blank" rel="noreferrer">
        🎉 IamAI 3.0 is released. Read more →
      </a>
    )
  },
  i18n: Object.entries(languageMap).map(([locale, text]) => ({
    locale,
    text,
  })),
  editLink: {
    text: () => useLocalesMap(editTextMap),
  },
  feedback: {
    content: () => useLocalesMap(feedbackLinkMap),
  },
  sidebar: {
    titleComponent({ title, type }) {
      if (type === 'separator') {
        return <span className="cursor-default">{title}</span>
      }
      return <>{title}</>
    },
    defaultMenuCollapseLevel: 2,
    toggleButton: true
  },
  footer: {
    text: (
      <div className="flex w-full flex-col items-center sm:items-start">
        <div>
          <a
            className="flex items-center gap-1 text-current"
            target="_blank"
            rel="noopener noreferrer"
            title="vercel.com homepage"
            href="https://vercel.com?utm_source=iamai.retrofor.space"
          >
            <span>Powered by</span>
            <svg height={20} viewBox="0 0 283 64" fill="none">
              <title>Vercel</title>
              <path
                fill="currentColor"
                d="M141.04 16c-11.04 0-19 7.2-19 18s8.96 18 20 18c6.67 0 12.55-2.64 16.19-7.09l-7.65-4.42c-2.02 2.21-5.09 3.5-8.54 3.5-4.79 0-8.86-2.5-10.37-6.5h28.02c.22-1.12.35-2.28.35-3.5 0-10.79-7.96-17.99-19-17.99zm-9.46 14.5c1.25-3.99 4.67-6.5 9.45-6.5 4.79 0 8.21 2.51 9.45 6.5h-18.9zM248.72 16c-11.04 0-19 7.2-19 18s8.96 18 20 18c6.67 0 12.55-2.64 16.19-7.09l-7.65-4.42c-2.02 2.21-5.09 3.5-8.54 3.5-4.79 0-8.86-2.5-10.37-6.5h28.02c.22-1.12.35-2.28.35-3.5 0-10.79-7.96-17.99-19-17.99zm-9.45 14.5c1.25-3.99 4.67-6.5 9.45-6.5 4.79 0 8.21 2.51 9.45 6.5h-18.9zM200.24 34c0 6 3.92 10 10 10 4.12 0 7.21-1.87 8.8-4.92l7.68 4.43c-3.18 5.3-9.14 8.49-16.48 8.49-11.05 0-19-7.2-19-18s7.96-18 19-18c7.34 0 13.29 3.19 16.48 8.49l-7.68 4.43c-1.59-3.05-4.68-4.92-8.8-4.92-6.07 0-10 4-10 10zm82.48-29v46h-9V5h9zM36.95 0L73.9 64H0L36.95 0zm92.38 5l-27.71 48L73.91 5H84.3l17.32 30 17.32-30h10.39zm58.91 12v9.69c-1-.29-2.06-.49-3.2-.49-5.81 0-10 4-10 10V51h-9V17h9v9.2c0-5.08 5.91-9.2 13.2-9.2z"
              />
            </svg>
          </a>
        </div>
        <p className="mt-6 text-xs">
          © {new Date().getFullYear()} The retrofor.
        </p>
      </div>
    )
  }
}

export default themeConfig;