import { useEffect, useRef } from 'react';
import * as THREE from 'three';

/* ------------------------------------------------------------------ */
/* MagicRings (React Bits) — used here as Dexter's ambient background */
/* ------------------------------------------------------------------ */

const vertexShader = `
void main() {
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

const fragmentShader = `
precision highp float;

uniform float uTime, uAttenuation, uLineThickness;
uniform float uBaseRadius, uRadiusStep, uScaleRate;
uniform float uOpacity, uNoiseAmount, uRotation, uRingGap;
uniform float uFadeIn, uFadeOut;
uniform float uMouseInfluence, uHoverAmount, uHoverScale, uParallax, uBurst;
uniform float uCoverageAlpha;
uniform vec2 uResolution, uMouse;
uniform vec3 uColor, uColorTwo;
uniform int uRingCount;

const float HP = 1.5707963;
const float CYCLE = 3.45;

float fade(float t) {
  return t < uFadeIn ? smoothstep(0.0, uFadeIn, t) : 1.0 - smoothstep(uFadeOut, CYCLE - 0.2, t);
}

float ring(vec2 p, float ri, float cut, float t0, float px) {
  float t = mod(uTime + t0, CYCLE);
  float r = ri + t / CYCLE * uScaleRate;
  float d = abs(length(p) - r);
  float a = atan(abs(p.y), abs(p.x)) / HP;
  float th = max(1.0 - a, 0.5) * px * uLineThickness;
  float h = (1.0 - smoothstep(th, th * 1.5, d)) + 1.0;
  d += pow(cut * a, 3.0) * r;
  return h * exp(-uAttenuation * d) * fade(t);
}

void main() {
  float px = 1.0 / min(uResolution.x, uResolution.y);
  vec2 p = (gl_FragCoord.xy - 0.5 * uResolution.xy) * px;
  float cr = cos(uRotation), sr = sin(uRotation);
  p = mat2(cr, -sr, sr, cr) * p;
  p -= uMouse * uMouseInfluence;
  float sc = mix(1.0, uHoverScale, uHoverAmount) + uBurst * 0.3;
  p /= sc;
  vec3 c = vec3(0.0);
  float coverage = 0.0;
  float rcf = max(float(uRingCount) - 1.0, 1.0);
  for (int i = 0; i < 10; i++) {
    if (i >= uRingCount) break;
    float fi = float(i);
    vec2 pr = p - fi * uParallax * uMouse;
    vec3 rc = mix(uColor, uColorTwo, fi / rcf);
    float ringAmount = ring(pr, uBaseRadius + fi * uRadiusStep, pow(uRingGap, fi), i == 0 ? 0.0 : 2.95 * fi, px);
    c = mix(c, rc, vec3(ringAmount));
    coverage = max(coverage, ringAmount);
  }
  c *= 1.0 + uBurst * 2.0;
  float n = fract(sin(dot(gl_FragCoord.xy + uTime * 100.0, vec2(12.9898, 78.233))) * 43758.5453);
  c += (n - 0.5) * uNoiseAmount;
  float intensity = max(c.r, max(c.g, c.b));
  vec3 emissiveColor = intensity > 0.0001 ? clamp(c / intensity, 0.0, 1.0) : vec3(0.0);
  vec3 outputColor = mix(emissiveColor, clamp(c, 0.0, 1.0), uCoverageAlpha);
  float outputAlpha = mix(intensity, coverage, uCoverageAlpha);
  gl_FragColor = vec4(outputColor, clamp(outputAlpha * uOpacity, 0.0, 1.0));
}
`;

function MagicRings({
  color = '#5B8DEF',
  colorTwo = '#9B6DFF',
  speed = 0.6,
  ringCount = 5,
  attenuation = 9,
  lineThickness = 1.4,
  baseRadius = 0.22,
  radiusStep = 0.09,
  scaleRate = 0.12,
  opacity = 0.55,
  blur = 0,
  noiseAmount = 0.05,
  rotation = 0,
  ringGap = 1.5,
  fadeIn = 0.7,
  fadeOut = 0.5,
  followMouse = true,
  mouseInfluence = 0.12,
  hoverScale = 1.05,
  parallax = 0.03,
  clickBurst = false,
  alphaMode = 'luminance',
}) {
  const mountRef = useRef(null);
  const propsRef = useRef(null);
  const mouseRef = useRef([0, 0]);
  const smoothMouseRef = useRef([0, 0]);
  const hoverAmountRef = useRef(0);
  const isHoveredRef = useRef(false);
  const burstRef = useRef(0);

  propsRef.current = {
    color, colorTwo, speed, ringCount, attenuation, lineThickness,
    baseRadius, radiusStep, scaleRate, opacity, noiseAmount,
    rotation, ringGap, fadeIn, fadeOut, followMouse, mouseInfluence,
    hoverScale, parallax, clickBurst, alphaMode,
  };

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    let renderer;
    try {
      renderer = new THREE.WebGLRenderer({ alpha: true });
    } catch {
      return;
    }

    renderer.setClearColor(0x000000, 0);
    mount.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-0.5, 0.5, 0.5, -0.5, 0.1, 10);
    camera.position.z = 1;

    const uniforms = {
      uTime: { value: 0 },
      uAttenuation: { value: 0 },
      uResolution: { value: new THREE.Vector2() },
      uColor: { value: new THREE.Color() },
      uColorTwo: { value: new THREE.Color() },
      uLineThickness: { value: 0 },
      uBaseRadius: { value: 0 },
      uRadiusStep: { value: 0 },
      uScaleRate: { value: 0 },
      uRingCount: { value: 0 },
      uOpacity: { value: 1 },
      uNoiseAmount: { value: 0 },
      uRotation: { value: 0 },
      uRingGap: { value: 1.6 },
      uFadeIn: { value: 0.5 },
      uFadeOut: { value: 0.75 },
      uMouse: { value: new THREE.Vector2() },
      uMouseInfluence: { value: 0 },
      uHoverAmount: { value: 0 },
      uHoverScale: { value: 1 },
      uParallax: { value: 0 },
      uBurst: { value: 0 },
      uCoverageAlpha: { value: 0 },
    };

    const material = new THREE.ShaderMaterial({ vertexShader, fragmentShader, uniforms, transparent: true });
    const quad = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), material);
    scene.add(quad);

    const resize = () => {
      const w = mount.clientWidth;
      const h = mount.clientHeight;
      const dpr = Math.min(window.devicePixelRatio, 2);
      renderer.setSize(w, h);
      renderer.setPixelRatio(dpr);
      uniforms.uResolution.value.set(w * dpr, h * dpr);
    };
    resize();
    window.addEventListener('resize', resize);

    const ro = new ResizeObserver(resize);
    ro.observe(mount);

    const onMouseMove = (e) => {
      const rect = mount.getBoundingClientRect();
      mouseRef.current[0] = (e.clientX - rect.left) / rect.width - 0.5;
      mouseRef.current[1] = -((e.clientY - rect.top) / rect.height - 0.5);
    };
    const onMouseEnter = () => { isHoveredRef.current = true; };
    const onMouseLeave = () => {
      isHoveredRef.current = false;
      mouseRef.current[0] = 0;
      mouseRef.current[1] = 0;
    };

    mount.addEventListener('mousemove', onMouseMove);
    mount.addEventListener('mouseenter', onMouseEnter);
    mount.addEventListener('mouseleave', onMouseLeave);

    let frameId = 0;
    let elapsed = 0;
    let lastT = 0;
    const animate = (t) => {
      frameId = requestAnimationFrame(animate);
      const p = propsRef.current;

      const dt = lastT === 0 ? 0 : Math.min(t - lastT, 100);
      lastT = t;
      elapsed += dt * 0.001 * p.speed;

      smoothMouseRef.current[0] += (mouseRef.current[0] - smoothMouseRef.current[0]) * 0.08;
      smoothMouseRef.current[1] += (mouseRef.current[1] - smoothMouseRef.current[1]) * 0.08;
      hoverAmountRef.current += ((isHoveredRef.current ? 1 : 0) - hoverAmountRef.current) * 0.08;

      uniforms.uTime.value = elapsed;
      uniforms.uAttenuation.value = p.attenuation;
      uniforms.uColor.value.set(p.color);
      uniforms.uColorTwo.value.set(p.colorTwo);
      uniforms.uLineThickness.value = p.lineThickness;
      uniforms.uBaseRadius.value = p.baseRadius;
      uniforms.uRadiusStep.value = p.radiusStep;
      uniforms.uScaleRate.value = p.scaleRate;
      uniforms.uRingCount.value = p.ringCount;
      uniforms.uOpacity.value = p.opacity;
      uniforms.uNoiseAmount.value = p.noiseAmount;
      uniforms.uRotation.value = (p.rotation * Math.PI) / 180;
      uniforms.uRingGap.value = p.ringGap;
      uniforms.uFadeIn.value = p.fadeIn;
      uniforms.uFadeOut.value = p.fadeOut;
      uniforms.uMouse.value.set(smoothMouseRef.current[0], smoothMouseRef.current[1]);
      uniforms.uMouseInfluence.value = p.followMouse ? p.mouseInfluence : 0;
      uniforms.uHoverAmount.value = hoverAmountRef.current;
      uniforms.uHoverScale.value = p.hoverScale;
      uniforms.uParallax.value = p.parallax;
      uniforms.uBurst.value = 0;
      uniforms.uCoverageAlpha.value = p.alphaMode === 'coverage' ? 1 : 0;

      renderer.render(scene, camera);
    };
    frameId = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(frameId);
      ro.disconnect();
      window.removeEventListener('resize', resize);
      mount.removeEventListener('mousemove', onMouseMove);
      mount.removeEventListener('mouseenter', onMouseEnter);
      mount.removeEventListener('mouseleave', onMouseLeave);
      mount.removeChild(renderer.domElement);
      renderer.dispose();
      material.dispose();
    };
  }, []);

  return (
    <div
      ref={mountRef}
      style={{
        position: 'absolute',
        inset: 0,
        width: '100%',
        height: '100%',
        filter: blur > 0 ? `blur(${blur}px)` : undefined,
      }}
    />
  );
}

/* ------------------------------------------------------------------ */
/* Dexter — écran d'accueil                                           */
/* ------------------------------------------------------------------ */

function RobotHeadIcon() {
  return (
    <svg width="34" height="34" viewBox="0 0 48 48" fill="none">
      <rect x="10" y="16" width="28" height="22" rx="8" fill="url(#dexterHeadGrad)" />
      <rect x="21" y="6" width="6" height="10" rx="3" fill="url(#dexterHeadGrad)" />
      <circle cx="24" cy="8" r="3" fill="#9B6DFF" />
      <circle cx="18.5" cy="26" r="3.4" fill="#0B0F1A" />
      <circle cx="29.5" cy="26" r="3.4" fill="#0B0F1A" />
      <rect x="17" y="33" width="14" height="2.6" rx="1.3" fill="#0B0F1A" opacity="0.55" />
      <defs>
        <linearGradient id="dexterHeadGrad" x1="10" y1="6" x2="38" y2="38" gradientUnits="userSpaceOnUse">
          <stop stopColor="#6EA0FF" />
          <stop offset="1" stopColor="#9B6DFF" />
        </linearGradient>
      </defs>
    </svg>
  );
}

export default function DexterWelcome({ plan = 'Free' }) {
  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        minHeight: '640px',
        borderRadius: '20px',
        overflow: 'hidden',
        background: 'radial-gradient(120% 140% at 50% 0%, #1B2547 0%, #0E1430 46%, #080B1C 100%)',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {/* halo animé en arrière-plan */}
      <MagicRings />

      {/* voile de contraste pour garder le texte lisible */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(60% 50% at 50% 42%, rgba(8,11,28,0.15) 0%, rgba(8,11,28,0.55) 65%, rgba(8,11,28,0.85) 100%)',
        }}
      />

      {/* badge plan */}
      <div
        style={{
          position: 'absolute',
          top: '24px',
          right: '24px',
          background: '#FFFFFF',
          color: '#0B0F1A',
          fontWeight: 700,
          fontSize: '13px',
          padding: '7px 16px',
          borderRadius: '999px',
          letterSpacing: '0.01em',
        }}
      >
        {plan}
      </div>

      {/* contenu central */}
      <div
        style={{
          position: 'relative',
          zIndex: 2,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          padding: '32px',
          maxWidth: '420px',
        }}
      >
        <div
          style={{
            width: '76px',
            height: '76px',
            borderRadius: '22px',
            background: 'rgba(255,255,255,0.95)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '28px',
            boxShadow: '0 0 0 1px rgba(255,255,255,0.08), 0 12px 30px rgba(74,108,247,0.25)',
          }}
        >
          <RobotHeadIcon />
        </div>

        <h1
          style={{
            color: '#FFFFFF',
            fontSize: '34px',
            fontWeight: 600,
            margin: 0,
            letterSpacing: '-0.01em',
          }}
        >
          Dexter
        </h1>

        <p
          style={{
            color: 'rgba(255,255,255,0.68)',
            fontSize: '15px',
            marginTop: '10px',
            marginBottom: '32px',
            lineHeight: 1.5,
          }}
        >
          Ton assistant pour la compta, la finance et plus encore
        </p>

        <button
          style={{
            background: '#FFFFFF',
            color: '#0B0F1A',
            fontWeight: 600,
            fontSize: '15px',
            padding: '13px 34px',
            borderRadius: '999px',
            border: 'none',
            cursor: 'pointer',
            boxShadow: '0 8px 20px rgba(0,0,0,0.25)',
          }}
        >
          Commencer
        </button>
      </div>

      {/* copyright */}
      <div
        style={{
          position: 'absolute',
          bottom: '20px',
          left: 0,
          right: 0,
          textAlign: 'center',
          color: 'rgba(255,255,255,0.35)',
          fontSize: '12px',
        }}
      >
        © 2026 Dexter. Tous droits réservés.
      </div>
    </div>
  );
}
