type Author = {
    name: string;
    link: `https://${string}`;
    github?: string;
    twitter?: string;
  };
  
  export const AUTHORS: Record<string, Author> = {
    eytan: {
      name: 'HsiangNianian',
      link: 'https://twitter.com/HsiangNianian',
      github: 'HsiangNianian',
    },
  };