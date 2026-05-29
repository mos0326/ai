import { useEffect, useRef } from "react";

interface Props {
  /** AIが話している間 true。星とオーブが脈動・発光する。 */
  speaking: boolean;
}

interface Star {
  r: number;
  ang: number;
  size: number;
  speed: number;
  phase: number;
  hue: number;
}

export default function GalaxyCanvas({ speaking }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const speakingRef = useRef(speaking);
  speakingRef.current = speaking;

  useEffect(() => {
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext("2d")!;
    let raf = 0;
    let w = 0;
    let h = 0;
    let cx = 0;
    let cy = 0;
    let stars: Star[] = [];
    let intensity = 0; // speaking を滑らかに追従させた 0..1

    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = canvas.clientWidth;
      h = canvas.clientHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      cx = w / 2;
      cy = h / 2;

      const count = Math.min(260, Math.max(80, Math.floor((w * h) / 9000)));
      const maxR = Math.hypot(w, h) / 2;
      stars = Array.from({ length: count }, () => {
        const r = Math.pow(Math.random(), 0.7) * maxR;
        return {
          r,
          ang: Math.random() * Math.PI * 2,
          size: Math.random() * 1.6 + 0.3,
          speed: (0.02 + Math.random() * 0.06) / (1 + r / 240),
          phase: Math.random() * Math.PI * 2,
          hue: 210 + Math.random() * 60,
        };
      });
    }

    function frame(tms: number) {
      const t = tms / 1000;
      const target = speakingRef.current ? 1 : 0;
      intensity += (target - intensity) * 0.05;

      // 背景の放射グラデーション
      const bg = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.hypot(w, h) / 1.5);
      bg.addColorStop(0, "#0a0a18");
      bg.addColorStop(0.5, "#06060f");
      bg.addColorStop(1, "#000000");
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, w, h);

      // 星（ゆっくり回転＋またたき、speaking時に脈動・増光）
      const rot = t * 0.012;
      for (const s of stars) {
        const a = s.ang + rot * s.speed * 8;
        const x = cx + Math.cos(a) * s.r;
        const y = cy + Math.sin(a) * s.r;
        const twinkle = 0.55 + 0.45 * Math.sin(t * 1.5 + s.phase);
        const pulse = 1 + intensity * 0.6 * Math.sin(t * 3 + s.phase);
        const alpha = Math.min(1, twinkle * (0.5 + 0.4 * intensity) + 0.15);
        const size = s.size * Math.max(0.2, pulse);
        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${s.hue}, 80%, ${70 + intensity * 15}%, ${alpha})`;
        ctx.shadowBlur = 6 + intensity * 10;
        ctx.shadowColor = `hsla(${s.hue}, 90%, 75%, ${alpha})`;
        ctx.fill();
      }
      ctx.shadowBlur = 0;

      // 中央のオーブ（呼吸＋speaking時に大きく脈動・発光）
      const baseR = Math.min(w, h) * 0.1;
      const breath = 0.5 + 0.5 * Math.sin(t * 0.8);
      const speak = 0.5 + 0.5 * Math.sin(t * 4.5);
      const orbR = baseR * (1 + 0.05 * breath + intensity * 0.28 * speak);

      const glow = ctx.createRadialGradient(cx, cy, 0, cx, cy, orbR * 3.2);
      glow.addColorStop(0, "rgba(225, 232, 255, 0.95)");
      glow.addColorStop(0.18, `rgba(150, 175, 255, ${0.55 + intensity * 0.3})`);
      glow.addColorStop(0.5, `rgba(90, 110, 220, ${0.16 + intensity * 0.18})`);
      glow.addColorStop(1, "rgba(40, 50, 120, 0)");
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(cx, cy, orbR * 3.2, 0, Math.PI * 2);
      ctx.fill();

      // 明るいコア
      ctx.beginPath();
      ctx.arc(cx, cy, orbR * 0.6, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(246, 249, 255, 0.9)";
      ctx.shadowBlur = 40 + intensity * 60;
      ctx.shadowColor = "rgba(170, 190, 255, 0.85)";
      ctx.fill();
      ctx.shadowBlur = 0;

      raf = requestAnimationFrame(frame);
    }

    resize();
    window.addEventListener("resize", resize);
    raf = requestAnimationFrame(frame);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return <canvas ref={canvasRef} className="galaxy" />;
}
