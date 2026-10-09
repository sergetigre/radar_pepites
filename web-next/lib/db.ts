import { neon } from "@neondatabase/serverless";

const databaseUrl = process.env.DATABASE_URL;

if (!databaseUrl) {
  throw new Error(
    "DATABASE_URL introuvable (.env.local en dev, variable d'environnement Vercel en prod)."
  );
}

// Driver HTTP Neon — une requête = un appel fetch, adapté aux Server
// Components / Route Handlers serverless de Next.js sur Vercel (pas de pool
// de connexions persistant à gérer, contrairement à SQLAlchemy côté
// Streamlit).
const sql = neon(databaseUrl);

// Comme node-postgres, le driver renvoie les colonnes NUMERIC/DECIMAL en
// string (pour ne pas perdre de précision) — mais le projet les utilise
// partout comme des nombres JS (tri, formatage, charts). Le driver expose un
// réglage `types` pour ça (CONFIG.md), mais en v1.2.0 il n'est lu que par
// `.query()`, pas par le tagged template `sql\`...\`` utilisé ici — on
// convertit donc les chaînes numériques après coup plutôt que de caster
// ::float8 dans chaque requête portée depuis db.py.
function coerceNumericStrings<T>(value: T): T {
  if (Buffer.isBuffer(value) || value instanceof Uint8Array) {
    return value;
  }
  if (Array.isArray(value)) {
    return value.map(coerceNumericStrings) as unknown as T;
  }
  if (value !== null && typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [key, v] of Object.entries(value as Record<string, unknown>)) {
      out[key] = coerceNumericStrings(v);
    }
    return out as T;
  }
  if (typeof value === "string" && /^-?\d+(\.\d+)?$/.test(value)) {
    return Number(value) as unknown as T;
  }
  return value;
}

// `query` est un tagged template : les valeurs interpolées sont
// automatiquement paramétrées (pas d'injection SQL possible).
export async function query<T = Record<string, unknown>>(
  strings: TemplateStringsArray,
  ...values: unknown[]
): Promise<T[]> {
  const rows = await sql(strings, ...values);
  return coerceNumericStrings(rows as T[]);
}
