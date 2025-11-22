import { cn } from '@/lib/utils';
import stonesImage from '@/assets/8_stones.png';

type OrbitSize = 'sm' | 'md' | 'lg';

const sizeMap: Record<OrbitSize, string> = {
  sm: 'h-32 w-32',
  md: 'h-44 w-44',
  lg: 'h-56 w-56',
};

interface PlanetOrbitProps {
  size?: OrbitSize;
  className?: string;
}

export const PlanetOrbit = ({ size = 'md', className }: PlanetOrbitProps) => {
  return (
    <img
      src={stonesImage}
      alt="8 stones"
      className={cn('object-contain', sizeMap[size], className)}
    />
  );
};
