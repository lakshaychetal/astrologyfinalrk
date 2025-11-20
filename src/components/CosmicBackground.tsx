import { useTheme } from '@/contexts/ThemeContext';

export const CosmicBackground = () => {
  const { theme } = useTheme();
  
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden">
      {theme === 'dark' ? (
        <>
          <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-purple-950 to-slate-900" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-purple-900/20 via-transparent to-transparent" />
          <div className="stars absolute inset-0" />
          <div className="twinkling absolute inset-0" />
        </>
      ) : (
        <>
          <div className="absolute inset-0 bg-gradient-to-br from-violet-50 via-purple-50 to-fuchsia-50" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-violet-200/30 via-transparent to-transparent" />
        </>
      )}
    </div>
  );
};
