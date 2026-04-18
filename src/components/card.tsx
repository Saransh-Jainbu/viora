import { HTMLAttributes } from 'react';
import { cn } from '../lib/utils';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hoverable?: boolean;
}

export function Card({ className, hoverable, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        'rounded-xl border border-border bg-card p-8',
        hoverable && 'transition-colors duration-200 hover:bg-accent',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
