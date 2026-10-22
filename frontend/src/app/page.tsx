import { Suspense } from "react";
import { SearchExperience } from "@/components/SearchExperience";

export default function Home() {
  return (
    <Suspense
      fallback={
        <p className="bg-paper px-6 py-16 text-center text-sm text-muted">Loading MeetMind…</p>
      }
    >
      <SearchExperience />
    </Suspense>
  );
}
