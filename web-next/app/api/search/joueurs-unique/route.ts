import { NextRequest, NextResponse } from "next/server";
import { searchJoueursUnique } from "@/lib/queries/search";

// Portage de web/utils/search.py::_search_joueurs_unique_fn (seuil 2 car.)
export async function GET(req: NextRequest) {
  const q = req.nextUrl.searchParams.get("q") ?? "";
  if (q.trim().length < 2) return NextResponse.json([]);
  const results = await searchJoueursUnique(q);
  return NextResponse.json(results);
}
