import React from 'react';
import { cn } from '@/lib/utils';

interface LiquidPanelProps {
  className?: string;
  children: React.ReactNode;
  asSection?: boolean;
}

export const LiquidPanel = ({ className, children, asSection = false }: LiquidPanelProps) => {
  const Tag = asSection ? 'section' : 'div';
  return (
    <Tag
      className={cn(
        'relative overflow-hidden rounded-[36px] border border-white/15 bg-white/5 shadow-[0_25px_80px_rgba(0,0,0,0.65)] backdrop-blur-3xl',
        className,
      )}
    >
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-white/15 via-transparent to-white/5" />
      <div className="relative z-10">{children}</div>
    </Tag>
  );
};
