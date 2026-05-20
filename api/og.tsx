import { ImageResponse } from '@vercel/og';

export const config = { runtime: 'edge' };

const BG = '#F1F1EC';
const INK = '#1F1F1D';
const INK_2 = '#555550';
const ACCENT = '#B89A45';
const FOREST = '#556142';

export default function handler(req: Request) {
  const { searchParams } = new URL(req.url);
  const lang = searchParams.get('lang') === 'en' ? 'en' : 'sk';
  const isEn = lang === 'en';
  const title =
    searchParams.get('title') ??
    (isEn ? 'Luggage Storage Bratislava' : 'Úschovňa batožiny Bratislava');
  const subtitle =
    searchParams.get('subtitle') ??
    (isEn ? '32 spots on one map' : '32 spotov na jednej mape');
  const eyebrow = searchParams.get('eyebrow') ?? 'Bratislava · live';
  const footnote =
    searchParams.get('footnote') ??
    (isEn
      ? 'From €5.90 · 24/7 lockers · book online'
      : 'Od 5,90 € · 24/7 boxy · online rezervácia');

  return new ImageResponse(
    (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          width: '100%',
          height: '100%',
          padding: '70px 80px',
          background: BG,
          backgroundImage:
            `radial-gradient(circle at 90% 10%, ${ACCENT}22 0%, transparent 45%), radial-gradient(circle at 5% 90%, ${FOREST}1A 0%, transparent 50%)`,
          fontFamily: 'serif',
          color: INK,
        }}
      >
        {/* Top row — brand + eyebrow */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 18,
              fontSize: 36,
              fontWeight: 600,
              letterSpacing: '-0.01em',
            }}
          >
            <svg
              width="44"
              height="44"
              viewBox="0 0 24 24"
              fill="none"
              stroke={INK}
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="4" y="10" width="16" height="11" rx="2.5" />
              <path d="M8 10V7a4 4 0 0 1 8 0v3" />
            </svg>
            <span>
              Lock<span style={{ color: ACCENT }}>&amp;</span>Go
            </span>
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 20px',
              borderRadius: 999,
              border: `1.5px solid ${INK}22`,
              fontSize: 20,
              color: INK_2,
            }}
          >
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: 999,
                background: FOREST,
              }}
            />
            {eyebrow}
          </div>
        </div>

        {/* Headline */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div
            style={{
              fontSize: 96,
              lineHeight: 1.02,
              fontStyle: 'italic',
              letterSpacing: '-0.02em',
              color: INK,
              maxWidth: '92%',
              display: 'flex',
            }}
          >
            {title}
          </div>
          <div
            style={{
              fontSize: 38,
              marginTop: 26,
              color: INK_2,
              maxWidth: '85%',
              display: 'flex',
            }}
          >
            {subtitle}
          </div>
        </div>

        {/* Footer */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: 26,
            color: INK_2,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <span
              style={{
                display: 'flex',
                padding: '6px 18px',
                borderRadius: 8,
                background: ACCENT,
                color: BG,
                fontSize: 24,
                fontWeight: 600,
                letterSpacing: '0.02em',
              }}
            >
              lockandgo.sk
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <span>{footnote}</span>
          </div>
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
      headers: {
        'cache-control':
          'public, immutable, no-transform, max-age=86400, s-maxage=86400',
      },
    },
  );
}
