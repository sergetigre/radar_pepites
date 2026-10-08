import { NextRequest, NextResponse } from "next/server";
import { searchGkUnique } from "@/lib/queries/search";

// Portage de web/utils/search.py::_search_gk_unique_fn (seuil 2 car.)
export async function GET(req: NextRequest) {
  const q = req.nextUrl.searchParams.get("q") ?? "";
  if (q.trim().length < 2) return NextResponse.json([]);
  const results = await searchGkUnique(q);
  return NextResponse.json(results);
}
