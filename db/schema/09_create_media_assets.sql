-- RadarPépites — Cache binaire des images Sofascore
-- Contexte : Sofascore (protégé Cloudflare, cf. commit scraper 573ad47)
-- bloque systématiquement les requêtes serveur-à-serveur (hotlink direct
-- ET proxy Next.js testés, tous deux en échec). Seul un vrai navigateur
-- (undetected-chromedriver, déjà utilisé par le scraper ETL) passe le
-- challenge. On télécharge donc une fois via etl/extract/
-- download_media_assets.py et on stocke le binaire ici — le site
-- Next.js sert ensuite ces images sans jamais recontacter Sofascore.

CREATE TABLE IF NOT EXISTS public.media_assets (
    kind            TEXT        NOT NULL,   -- 'player' | 'team' | 'unique-tournament'
    entity_id       BIGINT      NOT NULL,   -- player_id_ss / team_id_ss / tournament_id Sofascore
    content_type    TEXT        NOT NULL,   -- 'image/png', 'image/jpeg'...
    data            BYTEA       NOT NULL,
    date_maj        TIMESTAMP   DEFAULT NOW(),
    PRIMARY KEY (kind, entity_id)
);

COMMENT ON TABLE public.media_assets IS
    'Cache binaire des images Sofascore (logos clubs/ligues, photos joueurs), téléchargées une fois via navigateur réel et servies par le site sans dépendance Sofascore à l''exécution.';
