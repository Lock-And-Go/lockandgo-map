import { ImageResponse } from '@vercel/og';

const BG = '#F1F1EC';
const INK = '#1F1F1D';
const INK_2 = '#555550';
const ACCENT = '#B89A45';
const FOREST = '#556142';

const h = (type, props, children) => ({
  type,
  key: null,
  props: { ...(props || {}), children },
});

export default function handler(req) {
  const query = (req.url || '').split('?')[1] || '';
  const searchParams = new URLSearchParams(query);
  const lang = searchParams.get('lang') === 'en' ? 'en' : 'sk';
  const isEn = lang === 'en';
  const title =
    searchParams.get('title') ||
    (isEn ? 'Luggage Storage Bratislava' : 'Úschovňa batožiny Bratislava');
  const subtitle =
    searchParams.get('subtitle') ||
    (isEn ? '32 spots on one map' : '32 spotov na jednej mape');
  const eyebrow = searchParams.get('eyebrow') || 'Bratislava · live';
  const footnote =
    searchParams.get('footnote') ||
    (isEn
      ? 'From €5.90 · 24/7 lockers · book online'
      : 'Od 5,90 € · 24/7 boxy · online rezervácia');

  const brandSvg = h(
    'svg',
    {
      width: 44,
      height: 44,
      viewBox: '0 0 24 24',
      fill: 'none',
      stroke: INK,
      strokeWidth: '2.2',
      strokeLinecap: 'round',
      strokeLinejoin: 'round',
    },
    [
      h('rect', { x: 4, y: 10, width: 16, height: 11, rx: 2.5 }, null),
      h('path', { d: 'M8 10V7a4 4 0 0 1 8 0v3' }, null),
    ]
  );

  const brand = h(
    'div',
    {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 18,
        fontSize: 36,
        fontWeight: 600,
        letterSpacing: '-0.01em',
      },
    },
    [
      brandSvg,
      h('span', null, [
        'Lock',
        h('span', { style: { color: ACCENT } }, ' & '),
        'Go',
      ]),
    ]
  );

  const eyebrowChip = h(
    'div',
    {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '10px 20px',
        borderRadius: 999,
        border: `1.5px solid ${INK}22`,
        fontSize: 20,
        color: INK_2,
      },
    },
    [
      h(
        'div',
        {
          style: {
            width: 10,
            height: 10,
            borderRadius: 999,
            background: FOREST,
          },
        },
        null
      ),
      eyebrow,
    ]
  );

  const topRow = h(
    'div',
    {
      style: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      },
    },
    [brand, eyebrowChip]
  );

  const headline = h(
    'div',
    { style: { display: 'flex', flexDirection: 'column' } },
    [
      h(
        'div',
        {
          style: {
            fontSize: 96,
            lineHeight: 1.02,
            fontStyle: 'italic',
            letterSpacing: '-0.02em',
            color: INK,
            maxWidth: '92%',
            display: 'flex',
          },
        },
        title
      ),
      h(
        'div',
        {
          style: {
            fontSize: 38,
            marginTop: 26,
            color: INK_2,
            maxWidth: '85%',
            display: 'flex',
          },
        },
        subtitle
      ),
    ]
  );

  const footer = h(
    'div',
    {
      style: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: 26,
        color: INK_2,
      },
    },
    [
      h(
        'span',
        {
          style: {
            display: 'flex',
            padding: '6px 18px',
            borderRadius: 8,
            background: ACCENT,
            color: BG,
            fontSize: 24,
            fontWeight: 600,
            letterSpacing: '0.02em',
          },
        },
        'lockandgo.sk'
      ),
      h('span', null, footnote),
    ]
  );

  const root = h(
    'div',
    {
      style: {
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        width: '100%',
        height: '100%',
        padding: '70px 80px',
        background: BG,
        backgroundImage: `radial-gradient(circle at 90% 10%, ${ACCENT}22 0%, transparent 45%), radial-gradient(circle at 5% 90%, ${FOREST}1A 0%, transparent 50%)`,
        fontFamily: 'serif',
        color: INK,
      },
    },
    [topRow, headline, footer]
  );

  return new ImageResponse(root, {
    width: 1200,
    height: 630,
    headers: {
      'cache-control':
        'public, immutable, no-transform, max-age=86400, s-maxage=86400',
    },
  });
}
