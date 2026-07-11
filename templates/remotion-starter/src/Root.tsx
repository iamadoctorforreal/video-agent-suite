import { AbsoluteFill, Sequence, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';

export const Root: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = frame / fps;

  const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: 'clamp' });
  const scale = interpolate(frame, [0, 30], [0.8, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#1a1a2e',
        justifyContent: 'center',
        alignItems: 'center',
        fontFamily: 'Inter, sans-serif',
      }}
    >
      <Sequence from={0} durationInFrames={90}>
        <AbsoluteFill
          style={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            padding: 40,
          }}
        >
          <div
            style={{
              fontSize: 72,
              fontWeight: 'bold',
              color: 'white',
              textAlign: 'center',
              opacity: opacity,
              transform: `scale(${scale})`,
            }}
          >
            Video Agent Suite
          </div>
          <div
            style={{
              fontSize: 36,
              color: '#a0a0a0',
              textAlign: 'center',
              marginTop: 20,
              opacity: interpolate(frame, [15, 45], [0, 1], { extrapolateRight: 'clamp' }),
            }}
          >
            AI-Powered Video Creation
          </div>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
