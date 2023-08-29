import Document, { Head, Html, Main, NextScript } from 'next/document';
import { OrganizationJsonLd } from 'next-seo';
import { getCssText } from '@components/stitche.config';

export default class MyDocument extends Document {
  render() {
    return (
      <Html lang="en">
        <Head>
          <OrganizationJsonLd
            url="https://iamai.retrofor.space"
            logo="https://iamai.retrofor.space/logo.svg"
            name="The IamAI"
          />
          <style dangerouslySetInnerHTML={{ __html: getCssText() }} />
          <meta charSet="utf-8" />
          <link
            rel="alternate"
            type="application/rss+xml"
            title="RSS Feed for iamai"
            href="/feed.xml"
          />
        </Head>
        <body>
          <Main />
          <NextScript />
        </body>
      </Html>
    );
  }
}