import React, {useEffect, useState} from 'react';
import {Audio, Video} from '@remotion/media';
import {AbsoluteFill, Composition, Sequence, continueRender, delayRender, registerRoot, staticFile, useVideoConfig} from 'remotion';

const Hybrid = () => {
  const {fps} = useVideoConfig();
  const [fontHandle] = useState(() => delayRender('Noto Sans'));
  useEffect(() => {
    document.fonts.load('52px "Noto Sans"').then(() => continueRender(fontHandle));
  }, [fontHandle]);
  const titleStyle: React.CSSProperties = {
    justifyContent: 'center', alignItems: 'center',
    fontFamily: '"Noto Sans"', fontSize: 52, fontWeight: 400,
  };
  return (
    <AbsoluteFill style={{backgroundColor: '#101820'}}>
      <Sequence name="СТАРТ" from={0} durationInFrames={fps}>
        <AbsoluteFill style={{...titleStyle, color: '#ffffff'}}>СТАРТ</AbsoluteFill>
      </Sequence>
      <Video name="Manim pair" from={fps} durationInFrames={2 * fps}
        src={staticFile('insert.mp4')} muted playbackRate={1} objectFit="contain"
        style={{position: 'absolute', width: 640, height: 360}} />
      <Sequence name="ФИНИШ" from={3 * fps} durationInFrames={fps}>
        <AbsoluteFill style={{...titleStyle, color: '#66ddaa'}}>ФИНИШ</AbsoluteFill>
      </Sequence>
      <Audio name="660 Hz" from={3 * fps} src={staticFile('tone.wav')} />
    </AbsoluteFill>
  );
};

registerRoot(() => <Composition id="Hybrid" component={Hybrid}
  width={640} height={360} fps={30} durationInFrames={120} />);
