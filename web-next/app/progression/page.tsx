import { getProgressionJoueur } from "@/lib/queries/joueurs";
import { SearchCombobox } from "@/components/ui/SearchCombobox";
import { ProgressionView } from "@/components/player/ProgressionView";
import { Icon } from "@/components/ui/Icon";
import type { Metric } from "@/components/charts/LineProgression";

const METRIQUES_DEFAUT: Metric[] = [
  { col: "buts_p90", label: "Buts/90", color: "#2DAD7E" },
  { col: "xg_p90", label: "xG/90", color: "#5DCBA0" },
  { col: "passes_dec_p90", label: "Assists/90", color: "#E0B452" },
  { col: "key_passes_p90", label: "KP/90", color: "#4ECDC4" },
  { col: "dribbles_p90", label: "Drib/90", color: "#FF6B35" },
  { col: "tackles_p90", label: "Tac/90", color: "#E05252" },
];
const DEFAULT_SELECTED = ["Buts/90", "xG/90", "Assists/90"];

const TABLE_COLS = [
  { col: "saison_courte", label: "Saison" },
  { col: "minutes", label: "Minutes" },
  { col: "matchs_joues", label: "Matchs" },
  { col: "buts_p90", label: "Buts/90", highlight: true },
  { col: "xg_p90", label: "xG/90", highlight: true },
  { col: "passes_dec_p90", label: "Assists/90", highlight: true },
  { col: "xag_p90", label: "xAG/90", highlight: true },
  { col: "key_passes_p90", label: "KP/90", highlight: true },
  { col: "dribbles_p90", label: "Drib/90", highlight: true },
  { col: "tackles_p90", label: "Tac/90", highlight: true },
  { col: "interceptions_p90", label: "Int/90", highlight: true },
  { col: "score_pepite_corrige", label: "Score ★", highlight: true },
];

// Portage 1:1 de web/pages/04_Progression.py
export default async function ProgressionPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const joueurIdRaw = typeof sp.joueur_id === "string" ? sp.joueur_id : undefined;

  const data = joueurIdRaw ? await getProgressionJoueur(Number(joueurIdRaw)) : [];
  const nom = data[0]?.nom_court || data[0]?.nom_complet || "";
  const label = data[0] ? `${data[0].nom_complet}` : "";

  return (
    <div>
      <h1 className="text-[1.8rem] font-extrabold mb-2 flex items-center gap-2">
        <Icon name="trending_up" size={28} />
        Progression
      </h1>
      <p className="text-text-muted text-sm mb-6">
        Visualisez l&apos;évolution des statistiques d&apos;un joueur saison par saison.
      </p>

      <div className="mb-6">
        <SearchCombobox
          kind="joueurs"
          placeholder="Ex : Saka, Wirtz, Yamal..."
          defaultValue={label}
          unique
        />
      </div>

      {!joueurIdRaw ? (
        <p className="text-text-muted">
          Tapez le nom d&apos;un joueur pour afficher sa progression (2 lettres min.).
        </p>
      ) : data.length === 0 ? (
        <p className="text-warning">Aucune donnée de progression disponible.</p>
      ) : (
        <ProgressionView
          data={data}
          joueur={nom}
          metricsDefault={METRIQUES_DEFAUT}
          defaultSelectedLabels={DEFAULT_SELECTED}
          tableCols={TABLE_COLS}
        />
      )}
    </div>
  );
}
