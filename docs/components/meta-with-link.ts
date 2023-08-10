import { Meta } from './meta'

export type MetaWithLink = Omit<Meta, 'tags' | 'authors'> & {
    tags: string[];
    authors: string[];
    link: string;
  };

export default MetaWithLink;