import PixelBlast from './PixelBlast'

export default function Hero() {
  return (
    <div style={{ width: '100%', height: '100vh', position: 'relative' }}>
      <PixelBlast
        variant="circle"
        pixelSize={3}
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
        className=""
        style={{}}
      />
      <div className="absolute inset-0 flex flex-col items-center justify-center text-white z-10">
        <h1 className="text-6xl font-bold">Vortex</h1>
        <p className="text-xl mt-4">Next-gen event tracking</p>
      </div>
    </div>
  )
}
