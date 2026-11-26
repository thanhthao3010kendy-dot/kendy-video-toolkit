import {Composition} from 'remotion';
import {TarotIntro} from './TarotIntro';
import {LaBaiReveal} from './LaBaiReveal';

// Mọi bố cục: dọc 9:16, 1080×1920, 30 khung/giây
export const RemotionRoot = () => (
  <>
    <Composition
      id="TarotIntro"
      component={TarotIntro}
      durationInFrames={105}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{
        tieuDe: 'THÔNG ĐIỆP TAROT',
        phuDe: 'Kendy Huyền Học',
        anhLaBai: 'la-bai-mau.jpg',
      }}
    />
    <Composition
      id="LaBaiReveal"
      component={LaBaiReveal}
      durationInFrames={120}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{
        anhLaBai: 'la-bai-mau.jpg',
        tenLaBai: 'The Moon – Mặt Trăng',
        yNghia: 'Trực giác · Điều chưa sáng tỏ',
      }}
    />
  </>
);
