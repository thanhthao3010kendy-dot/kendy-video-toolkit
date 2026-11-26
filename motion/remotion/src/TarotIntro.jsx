import {AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {MAU, NenSao, fadeInOut, useFonts} from './shared';

const CARD_W = 520;
const CARD_H = Math.round(CARD_W * 1.727);

// Đoạn mở đầu 3,5 s: lá bài bay lên, lật mặt, tiêu đề hiện dần. Hiệu ứng vừa phải.
export const TarotIntro = ({tieuDe, phuDe, anhLaBai}) => {
  useFonts();
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  const len = spring({frame, fps, config: {damping: 18, stiffness: 70}});
  const lat = spring({frame: frame - 22, fps, config: {damping: 16, stiffness: 60}});
  const goc = interpolate(lat, [0, 1], [180, 0]);
  const y = interpolate(len, [0, 1], [260, 0]);
  const thoGap = 1 + 0.012 * Math.sin(frame / 10);
  const chu = interpolate(frame, [48, 70], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const toanCanh = fadeInOut(frame, durationInFrames, 8, 10);

  const mat = {
    position: 'absolute',
    inset: 0,
    borderRadius: 26,
    overflow: 'hidden',
    boxShadow: '0 30px 80px rgba(0,0,0,.55), 0 0 60px rgba(216,190,140,.25)',
  };

  return (
    <AbsoluteFill style={{opacity: toanCanh}}>
      <NenSao />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', perspective: 1800}}>
        {/* Lớp ngoài: bay lên + mờ dần; lớp trong: xoay 3D. Mặt hiển thị chọn theo góc (ổn định mọi trình duyệt). */}
        <div style={{marginTop: -220, transform: `translateY(${y}px) scale(${thoGap})`, opacity: len}}>
          <div style={{width: CARD_W, height: CARD_H, position: 'relative', transform: `rotateY(${goc}deg)`}}>
            {goc > 90 ? (
              <div style={{...mat, transform: 'scaleX(-1)', background: `linear-gradient(160deg, #0F5C63, #062A2F)`, border: `6px solid ${MAU.vang}`}}>
                <div style={{position: 'absolute', inset: 28, border: `2px solid ${MAU.vang}`, borderRadius: 14, opacity: 0.7}} />
                <div style={{position: 'absolute', top: '50%', left: '50%', width: 150, height: 150, marginLeft: -75, marginTop: -75, borderRadius: '50%', border: `3px solid ${MAU.vang}`, boxShadow: `0 0 40px ${MAU.vang}`}} />
              </div>
            ) : (
              <div style={mat}>
                <Img src={staticFile(anhLaBai)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
              </div>
            )}
          </div>
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 420, opacity: chu}}>
        <div style={{fontFamily: 'Cormorant Garamond', fontWeight: 600, fontSize: 92, color: MAU.vang, letterSpacing: 6, textAlign: 'center', textWrap: 'balance', padding: '0 60px', transform: `translateY(${(1 - chu) * 24}px)`, textShadow: '0 4px 24px rgba(0,0,0,.6)'}}>
          {tieuDe}
        </div>
        <div style={{marginTop: 18, fontFamily: 'Be Vietnam Pro', fontWeight: 500, fontSize: 44, color: MAU.chu, letterSpacing: 2, opacity: 0.9}}>
          {phuDe}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
