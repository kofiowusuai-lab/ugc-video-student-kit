import React from 'react';
import {AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame, interpolate} from 'remotion';
export type UgcVerticalProps = {videoSrc: string; headline: string; cta: string; accent: string; captions: Array<{text: string; startFrame: number; endFrame: number}>};
export const UgcVertical: React.FC<UgcVerticalProps> = ({videoSrc, headline, cta, accent, captions}) => {
  const frame = useCurrentFrame();
  const ctaOpacity = interpolate(frame, [330, 360], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const caption = captions.find((item) => frame >= item.startFrame && frame < item.endFrame);
  return <AbsoluteFill style={{backgroundColor: '#000', fontFamily: 'Arial, sans-serif'}}>
    <OffthreadVideo src={staticFile(videoSrc)} />
    <div style={{position: 'absolute', top: 96, left: 72, right: 72, color: '#fff', fontSize: 64, fontWeight: 800, textShadow: '0 3px 16px #000'}}>{headline}</div>
    {caption ? <div style={{position: 'absolute', bottom: 360, left: 72, right: 72, color: '#fff', fontSize: 54, lineHeight: 1.12, fontWeight: 800, textAlign: 'center', textShadow: '0 4px 18px #000'}}>{caption.text}</div> : null}
    <div style={{position: 'absolute', bottom: 140, left: 96, right: 96, opacity: ctaOpacity, background: accent, color: '#111', borderRadius: 28, padding: 28, textAlign: 'center', fontSize: 48, fontWeight: 800}}>{cta}</div>
  </AbsoluteFill>;
};
