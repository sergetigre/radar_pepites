import { FormationCard } from "./FormationCard";
import { Icon } from "@/components/ui/Icon";
import type { ClassementRow } from "@/lib/queries/joueurs";
import type { TopGkScoreRow } from "@/lib/queries/gardiens";

// DM (Milieu défensif) volontairement absent : aucun joueur n'est jamais
// classé DM dans la base actuelle (le pipeline de classification des
// postes fait retomber tous les DM sur CM avant chargement — problème
// identifié côté Streamlit, pas corrigé ici). Formation à 2 CM + 1 AM.
const POSTE_LABELS: Record<string, string> = {
  FW: "Avant-centre",
  LW: "Ailier gauche",
  RW: "Ailier droit",
  AM: "Milieu offensif",
  CM: "Milieu central",
  CB: "Défenseur central",
  LB: "Latéral gauche",
  RB: "Latéral droit",
};

function topNPoste(data: ClassementRow[], poste: string, n = 3): ClassementRow[] {
  return data
    .filter((r) => r.poste_id === poste)
    .sort((a, b) => (b.score_corrige ?? -Infinity) - (a.score_corrige ?? -Infinity))
    .slice(0, n);
}

// Portage 1:1 de slots_poste() : découpe le top n_total d'un poste en
// n_slots cartes distinctes (slot 0 prend les rangs 0/2, slot 1 les rangs
// 1/3, ...) pour que les 2 titulaires d'un même poste (CB, CM) n'aient pas
// la même doublure.
function slotsPoste(data: ClassementRow[], poste: string, nSlots: number, nTotal: number): ClassementRow[][] {
  const tops = topNPoste(data, poste, nTotal);
  const slots: ClassementRow[][] = [];
  for (let slot = 0; slot < nSlots; slot++) {
    const picked: ClassementRow[] = [];
    for (let idx = slot; idx < tops.length; idx += nSlots) picked.push(tops[idx]);
    slots.push(picked);
  }
  return slots;
}

function FormationRow({ titre, children }: { titre: React.ReactNode; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-[0.65rem] font-bold uppercase tracking-[2px] text-text-muted mt-4 mb-2">
        {titre}
      </div>
      <div className="flex gap-2.5 flex-wrap justify-center items-start">{children}</div>
    </div>
  );
}

export function OnzeType({
  data,
  gkTop,
  saison,
}: {
  data: ClassementRow[];
  gkTop: TopGkScoreRow[];
  saison: string;
}) {
  const cbSlots = slotsPoste(data, "CB", 2, 4);
  const cmSlots = slotsPoste(data, "CM", 2, 4);

  return (
    <div>
      <FormationRow
        titre={
          <>
            <Icon name="sports_handball" size={14} /> Gardien
          </>
        }
      >
        <FormationCard players={gkTop} urlBase="/radar-gk" posteLabel="Gardien" saison={saison} />
      </FormationRow>

      <FormationRow
        titre={
          <>
            <Icon name="shield" size={14} /> Défense
          </>
        }
      >
        <FormationCard
          players={topNPoste(data, "LB", 3)}
          urlBase="/radar-joueur"
          posteLabel={POSTE_LABELS.LB}
          saison={saison}
        />
        <FormationCard players={cbSlots[0]} urlBase="/radar-joueur" posteLabel={POSTE_LABELS.CB} saison={saison} />
        <FormationCard players={cbSlots[1]} urlBase="/radar-joueur" posteLabel={POSTE_LABELS.CB} saison={saison} />
        <FormationCard
          players={topNPoste(data, "RB", 3)}
          urlBase="/radar-joueur"
          posteLabel={POSTE_LABELS.RB}
          saison={saison}
        />
      </FormationRow>

      <FormationRow
        titre={
          <>
            <Icon name="sync_alt" size={14} /> Milieu
          </>
        }
      >
        <FormationCard players={cmSlots[0]} urlBase="/radar-joueur" posteLabel={POSTE_LABELS.CM} saison={saison} />
        <FormationCard players={cmSlots[1]} urlBase="/radar-joueur" posteLabel={POSTE_LABELS.CM} saison={saison} />
        <FormationCard
          players={topNPoste(data, "AM", 3)}
          urlBase="/radar-joueur"
          posteLabel={POSTE_LABELS.AM}
          saison={saison}
        />
      </FormationRow>

      <FormationRow
        titre={
          <>
            <Icon name="bolt" size={14} /> Attaque
          </>
        }
      >
        <FormationCard
          players={topNPoste(data, "LW", 3)}
          urlBase="/radar-joueur"
          posteLabel={POSTE_LABELS.LW}
          saison={saison}
        />
        <FormationCard
          players={topNPoste(data, "FW", 3)}
          urlBase="/radar-joueur"
          posteLabel={POSTE_LABELS.FW}
          saison={saison}
        />
        <FormationCard
          players={topNPoste(data, "RW", 3)}
          urlBase="/radar-joueur"
          posteLabel={POSTE_LABELS.RW}
          saison={saison}
        />
      </FormationRow>
    </div>
  );
}
