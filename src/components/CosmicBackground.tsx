export const CosmicBackground = () => {
  const subtleOrbs = ['left-0 top-24 w-72 h-72', 'right-8 top-10 w-64 h-64', 'left-1/2 top-0 w-48 h-48'];

  return (
    <div className="fixed inset-0 -z-10 overflow-hidden bg-[#010101]">
      <div className="absolute inset-0 bg-gradient-to-b from-[#030303] via-[#050505] to-[#010101]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.1),_transparent_60%)]" />
      <div className="absolute inset-0 pointer-events-none">
        {subtleOrbs.map((cls, index) => (
          <span
            key={index}
            className={`absolute ${cls} rounded-full border border-white/10 bg-white/5 opacity-40 blur-2xl`}
          />
        ))}
      </div>
      <div className="absolute inset-0">
        <div className="stars absolute inset-0" />
        <div className="twinkling absolute inset-0" />
      </div>
    </div>
  );
};
