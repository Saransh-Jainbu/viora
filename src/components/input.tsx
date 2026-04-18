import { InputHTMLAttributes, forwardRef } from 'react';
import { cn } from '../lib/utils';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(
          'w-full px-4 py-2.5 rounded-xl border border-border bg-card',
          'focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary',
          'transition-colors duration-200',
          'placeholder:text-muted-foreground text-sm',
          className
        )}
        {...props}
      />
    );
  }
);

Input.displayName = 'Input';
