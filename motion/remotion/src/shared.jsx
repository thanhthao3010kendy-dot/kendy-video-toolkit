import {useEffect, useState} from 'react';
import {AbsoluteFill, continueRender, delayRender, interpolate, random, staticFile, useCurrentFrame} from 'remotion';

// Bảng màu Kendy Huyền Học: xanh cổ vịt đậm, kem sáng, vàng champagne
export const MAU = {
  nen1: '#0F5C63',
  nen2: '#062A2F',
  vang: '#D8BE8C',
  chu: '#F6EFE0',
};

// Nạp phông chữ cục bộ (hỗ trợ đủ dấu tiếng Việt) trước khi dựng khung hình
const FONTS = [
  ['Be Vietnam Pro', 'BeVietnamPro-Medium.ttf', '500'],
  ['Be Vietnam Pro', 'BeVietnamPro-Bold.ttf', '700'],
  ['Cormorant Garamond', 'CormorantGaramond-SemiBold.ttf', '600'],
];

export const useFonts = () => {
  const [handle] = useState(() => delayRender('Nạp phông chữ'));
  useEffect(() => {
    Promise.all(
      FONTS.map(([family, file, weight]) => {
        const f = new FontFace(family, `url(${staticFile(file)})`, {weight});
        return f.load().then((loaded) => document.fonts.add(loaded));
      }),
    )
      .then(() => continueRender(handle))
      .catch((err) => {
        console.error(err);
        continueRender(handle);
      });
  }, [handle]);
};

// Nền tím đêm + sao lấp lánh nhẹ (vị trí cố định theo hạt giống → mỗi lần dựng giống hệt nhau)
export const NenSao = ({soSao = 70}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{background: `radial-gradient(ellipse at 50% 38%, ${MAU.nen1} 0%, ${MAU.nen2} 72%)`}}
    >
      {new Array(soSao).fill(0).map((_, i) => {
        const x = random(`x${i}`) * 1080;
        const y = random(`y${i}`) * 1920;
        const r = 1 + random(`r${i}`) * 2.2;
        const pha = random(`p${i}`) * Math.PI * 2;
        const sang = 0.25 + 0.55 * (0.5 + 0.5 * Math.sin(frame / 14 + pha));
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: r * 2,
              height: r * 2,
              borderRadius: '50%',
              background: MAU.vang,
              opacity: sang,
              boxShadow: `0 0 ${r * 4}px ${MAU.vang}`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

export const fadeInOut = (frame, total, vao = 12, ra = 12) =>
  interpolate(frame, [0, vao, total - ra, total], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
