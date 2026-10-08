import { NextRequest, NextResponse } from "next/server";
import { searchGk } from "@/lib/queries/search";

// Portage de web/utils/search.py::_search_gk_fn (seuil 2 caractères)
export async function GET(req: NextRequest) {
  const q = req.nextUrl.searchParams.get("q") ?? "";
  if (q.trim().length < 2) return NextResponse.json([]);
  const results = await searchGk(q);
  return NextResponse.json(results);
}
