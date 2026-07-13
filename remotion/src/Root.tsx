import React from 'react';
import {Composition} from 'remotion';
import {UgcVertical, UgcVerticalProps} from './UgcVertical';

export const Root: React.FC = () => (
  <Composition id="UgcVertical" component={UgcVertical} width={1080} height={1920} fps={30} durationInFrames={450}
    defaultProps={{videoSrc: '', headline: '', cta: '', accent: '#ffffff', captions: []} satisfies UgcVerticalProps} />
);
