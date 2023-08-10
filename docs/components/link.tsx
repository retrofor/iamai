import { ComponentProps, ReactElement } from 'react';
import clsx from 'clsx';

export const Link = ({
  children,
  href,
  className,
  ...props
}: Omit<ComponentProps<'a'>, 'ref'>): ReactElement => {
  return (
    <a href={href} className={clsx('text-[#1cc8ee] hover:underline', className)} {...props}>
      {children}
    </a>
  );
};