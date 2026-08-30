import PixelBlast from '@components/PixelBlast';

interface HeroProps {
  children: React.ReactNode;
  className?: string;
}

function Hero({ children, className = '' }: HeroProps) {
  return (
    <div className={`relative w-full h-screen overflow-hidden ${className}`}>
      <PixelBlast
        variant="circle"
        pixelSize={6}
        color="#06B6D4"
        patternScale={3}
        patternDensity={1.2}
        pixelSizeJitter={0.5}
        enableRipples
        rippleSpeed={0.4}
        rippleThickness={0.12}
        rippleIntensityScale={1.5}
        liquid
        liquidStrength={0.12}
        liquidRadius={1.2}
        liquidWobbleSpeed={5}
        speed={0.6}
        edgeFade={0.25}
        transparent
      />
      <div className="absolute inset-0 flex items-center justify-center">
        {children}
      </div>
    </div>
  );
}

export default Hero;
