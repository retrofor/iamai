// -- dummy exported default, if necessary
export default function Dummy(props){
    return null;
};

export const getServerSideProps = async (context) => {
    const { res } = context;
    const sitemapString = createSitemap();

    res.setHeader("Content-Type", "text/xml");
    res.write(sitemapString);
    res.end();

    return {
        props: {},
    };
};