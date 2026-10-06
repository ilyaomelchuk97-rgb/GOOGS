// Private Render-to-D1 bridge. Never put BRIDGE_TOKEN in browser code or Git.
const allow = { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' };
function json(body, status=200) { return new Response(JSON.stringify(body), { status, headers: allow }); }
function validStatements(items) {
  if (!Array.isArray(items) || !items.length || items.length > 40) throw Error('1–40 SQL statements required');
  return items.map(item => {
    if (!item || typeof item.sql !== 'string' || !item.sql.trim() || item.sql.length > 100000 ||
        !Array.isArray(item.params) || item.params.length > 100 ||
        item.params.some(x => x !== null && typeof x !== 'string' && typeof x !== 'number' && typeof x !== 'boolean')) {
      throw Error('Invalid SQL or bindings');
    }
    return item;
  });
}
export default {
  async fetch(request, env) {
    const path = new URL(request.url).pathname;
    if (path !== '/v1/query' && path !== '/v1/batch') return json({ error:'Not found' },404);
    if (request.method !== 'POST') return json({ error:'Method not allowed' },405);
    if (!env.BRIDGE_TOKEN || request.headers.get('X-Forma-Bridge') !== env.BRIDGE_TOKEN) return json({ error:'Forbidden' },403);
    if (Number(request.headers.get('content-length') || 0) > 512000) return json({ error:'Request too large' },413);
    try {
      const raw = await request.text();
      if (new TextEncoder().encode(raw).length > 512000) return json({ error:'Request too large' },413);
      const body = JSON.parse(raw);
      const items = validStatements(path === '/v1/query' ? [body] : body.statements);
      const stmts = items.map(({ sql,params }) => env.DB.prepare(sql).bind(...params));
      const results = path === '/v1/query' ? [await stmts[0].run()] : await env.DB.batch(stmts);
      return json({ results:results.map(result => ({
        rows:result.results ?? [], lastrowid:result.meta?.last_row_id ?? null,
        changes:result.meta?.changes ?? 0
      })) });
    } catch (err) {
      // SQL can contain sensitive data. Never echo statement or bindings to clients/logs.
      const message=String(err?.message || 'Query failed');
      const conflict=/UNIQUE constraint|FOREIGN KEY constraint|CHECK constraint|NOT NULL constraint/i.test(message);
      return json({ error:conflict?'Database constraint violated':'Database operation failed', conflict },conflict?409:400);
    }
  },
  async scheduled(_event, env, ctx) {
    if (!env.RENDER_HEALTH_URL) return;
    ctx.waitUntil((async () => {
      try {
        const url=new URL(env.RENDER_HEALTH_URL);
        if (url.protocol!=='https:' || !url.hostname.endsWith('.onrender.com') || url.pathname!=='/health') return;
        await fetch(url, { method:'GET', headers: { 'Cache-Control':'no-store' }, signal:AbortSignal.timeout(20000) });
      } catch (_) { /* health attempts are best-effort; do not expose URL or secrets */ }
    })());
  }
};
