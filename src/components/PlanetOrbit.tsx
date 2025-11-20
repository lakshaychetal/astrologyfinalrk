import { cn } from '@/lib/utils';

type OrbitSize = 'sm' | 'md' | 'lg';

const sizeMap: Record<OrbitSize, string> = {
  sm: 'h-32 w-32',
  md: 'h-44 w-44',
  lg: 'h-56 w-56',
};

const radiusMap: Record<OrbitSize, number> = {
  sm: 44,
  md: 56,
  lg: 72,
};

const planets = ['Mercury', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn', 'Neptune'];

interface PlanetOrbitProps {
  size?: OrbitSize;
  className?: string;
}

export const PlanetOrbit = ({ size = 'md', className }: PlanetOrbitProps) => {
  return (
    <div
      className={cn('relative flex items-center justify-center', sizeMap[size], className)}
    >
      <div className="absolute inset-0 rounded-full border border-white/15" />
      <div className="absolute inset-4 rounded-full border border-white/5 opacity-60" />
      {planets.map((planet, index) => {
        const angle = (360 / planets.length) * index;
        return (
          <span
            key={planet}
            className="absolute h-3 w-3 rounded-full bg-white shadow-[0_0_25px_rgba(255,255,255,0.6)]"
            style={{
              transform: `translate(-50%, -50%) rotate(${angle}deg) translate(${radiusMap[size]}px) rotate(-${angle}deg)`,
            }}
          ></span>
        );
      })}
    </div>
  );
};
