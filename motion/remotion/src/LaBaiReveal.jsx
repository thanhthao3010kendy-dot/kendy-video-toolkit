import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {MAU, NenSao, fadeInOut, useFonts} from './shared';

// Thẻ giới thiệu một lá bài (4 s): ảnh lá bài gốc độ nét cao + tên + ý nghĩa ngắn.
export const LaBaiReveal = ({anhLaBai, tenLaBai, yNghia}) => {
  useFonts();
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const vao = spring({frame, fps, config: {damping: 20, stiffness: 80}});
  const scale = interpolate(vao, [0, 1], [0.92, 1]);
  const chu = interpolate(frame, [18, 36], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{opacity: fadeInOut(frame, durationInFrames, 8, 10)}}>
      <NenSao soSao={45} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
        <div style={{width: 600, height: 1036, marginTop: -200, borderRadius: 28, overflow: 'hidden', transform: `scale(${scale})`, opacity: vao, boxShadow: '0 30px 90px rgba(0,0,0,.6), 0 0 50px rgba(216,190,140,.22)'}}>
          <Img src={staticFile(anhLaBai)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 300, opacity: chu}}>
        <div style={{fontFamily: 'Cormorant Garamond', fontWeight: 600, fontSize: 80, color: MAU.vang, textAlign: 'center', textWrap: 'balance', padding: '0 60px'}}>{tenLaBai}</div>
        <div style={{marginTop: 14, fontFamily: 'Be Vietnam Pro', fontWeight: 500, fontSize: 42, color: MAU.chu, opacity: 0.9, textAlign: 'center', padding: '0 80px', textWrap: 'balance'}}>{yNghia}</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
