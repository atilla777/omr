import React from 'react';
import {Audio} from '@remotion/media';
import {
  Composition, Interactive, Track, interpolate, registerRoot,
  staticFile, useCurrentFrame, useVideoConfig,
} from 'remotion';

const CardInner = ({text, fontSize, color}: {
  text: string;
  fontSize: number;
  color: string;
}) => {
  const frame = useCurrentFrame();
  return <div style={{
    fontFamily: '"Noto Sans", sans-serif', fontWeight: 400,
    fontSize, color, lineHeight: 1.2,
    opacity: interpolate(frame, [0, 9], [0, 1], {
      extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    }),
  }}>{text}</div>;
};

const Card = Interactive.create({Component: CardInner, layout: 'absolute-fill'});
const cardStyle: React.CSSProperties = {
  backgroundColor: '#101820', justifyContent: 'center', alignItems: 'center',
  padding: 40, boxSizing: 'border-box',
};

const TwoCards = () => {
  const {fps} = useVideoConfig();
  return <>
    <Track name="Cards">
      <Card name="OMR" durationInFrames={2 * fps}
        text="OMR" fontSize={64} color="#ffffff" style={cardStyle} />
      <Card name="ГОТОВО" from={2 * fps} durationInFrames={2 * fps}
        text="ГОТОВО" fontSize={52} color="#66ddaa" style={cardStyle} />
    </Track>
    <Audio name="660 Hz tone" from={2 * fps} durationInFrames={0.2 * fps}
      src={staticFile('tone.wav')} />
  </>;
};

const Root = () => <>
  <Composition id="TwoCards" component={TwoCards}
    width={640} height={360} fps={30} durationInFrames={120} />
  <Composition id="Card" component={Card}
    width={640} height={360} fps={30} durationInFrames={60}
    defaultProps={{text: 'OMR', fontSize: 64, color: '#ffffff', style: cardStyle}} />
</>;

registerRoot(Root);
