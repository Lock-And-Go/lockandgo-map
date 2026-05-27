// IndexNow ping — notifies Bing/Yandex/Seznam of URL changes.
// Triggered daily via Vercel Cron (see vercel.json `crons`) and manually
// via GET /api/indexnow (or POST with custom { urls: [...] } payload).
//
// Spec: https://www.indexnow.org/documentation

export const config = { runtime: 'nodejs' };

const KEY = '8e0f424d53f3b944204762bdc7e87310';
const HOST = 'lockandgo.sk';
const KEY_LOCATION = `https://${HOST}/${KEY}.txt`;
const ENDPOINT = 'https://api.indexnow.org/IndexNow';
const SITEMAP_URL = `https://${HOST}/sitemap.xml`;

async function loadSitemapUrls() {
  const res = await fetch(SITEMAP_URL, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`sitemap fetch failed: HTTP ${res.status}`);
  }
  const xml = await res.text();
  const matches = [...xml.matchAll(/<loc>\s*([^<\s]+)\s*<\/loc>/g)];
  return matches.map((m) => m[1].trim()).filter((u) => u.startsWith(`https://${HOST}`));
}

async function pingIndexNow(urls) {
  const payload = {
    host: HOST,
    key: KEY,
    keyLocation: KEY_LOCATION,
    urlList: urls,
  };
  const res = await fetch(ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify(payload),
  });
  const text = await res.text();
  return { status: res.status, ok: res.ok, body: text.slice(0, 200) };
}

export default async function handler(req, res) {
  // Vercel cron jobs send an Authorization: Bearer <CRON_SECRET> header.
  // If CRON_SECRET is set in env, require it for non-GET runs to prevent abuse.
  const auth = req.headers.authorization || '';
  const secret = process.env.CRON_SECRET;
  const isCron = secret && auth === `Bearer ${secret}`;
  const isManualGet = req.method === 'GET';

  if (!isCron && !isManualGet) {
    return res.status(401).json({ ok: false, error: 'unauthorized' });
  }

  try {
    let urls;

    // Allow POST with custom { urls: [...] } when authenticated
    if (req.method === 'POST' && req.body && Array.isArray(req.body.urls)) {
      urls = req.body.urls.filter((u) => typeof u === 'string' && u.startsWith(`https://${HOST}`));
    } else {
      urls = await loadSitemapUrls();
    }

    if (!urls.length) {
      return res.status(200).json({ ok: true, pinged: 0, message: 'no URLs to submit' });
    }

    const result = await pingIndexNow(urls);

    return res.status(200).json({
      ok: result.ok,
      indexNowStatus: result.status,
      indexNowResponse: result.body,
      pinged: urls.length,
      sample: urls.slice(0, 3),
      trigger: isCron ? 'cron' : 'manual',
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    return res.status(500).json({ ok: false, error: String(err && err.message || err) });
  }
}
