"""Đo độ hạ nhạc nền khi đang nói / khi nghỉ (kiểm chứng ducking)."""
import subprocess, sys, numpy as np
voice, music, keychain, sc = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
def pcm(args, sr=8000):
    return np.frombuffer(subprocess.run(['ffmpeg','-v','error']+args+['-ac','1','-ar',str(sr),'-f','f32le','-'],stdout=subprocess.PIPE).stdout,dtype=np.float32)
g=(f"[0:a]aresample=48000,{keychain}[key];[1:a]aresample=48000,aformat=channel_layouts=stereo,volume=-22dB[m];"
   f"[m][key]{sc}[md]")
d=pcm(['-i',voice,'-stream_loop','-1','-i',music,'-filter_complex',g,'-map','[md]','-t','30'])
p=pcm(['-stream_loop','-1','-i',music,'-af','volume=-22dB','-t','30'])
v=pcm(['-i',voice,'-t','30'])
n=min(len(v),len(d),len(p))//400
f=lambda x:np.sqrt((x[:n*400].reshape(n,400)**2).mean(1)+1e-12)
ev,ed,ep=f(v),f(d),f(p)
speech=20*np.log10(ev)>-45
gain=20*np.log10(ed/ep)
print(f"khi nói: {np.median(gain[speech]):.1f} dB | khi nghỉ: {np.median(gain[~speech]):.1f} dB")
