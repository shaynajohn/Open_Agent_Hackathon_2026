"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { apiBaseUrl, apiIsReachable, searchPeople } from "@/lib/api";
import type { SearchResponse } from "@/lib/types";
import { CandidateCard } from "@/components/CandidateCard";

const SAMPLE_QUERY =
  "I want to meet a Product Manager at Stripe who works on AI products. I'm interested in transitioning from data science into product management.";

const autoRan = new Set<string>();

type Tone = "warm" | "direct" | "curious";

export function SearchExperience() {
  const params = useSearchParams();
  const initialQuery = params.get("q")?.trim() ?? "";
  const initialBackground = params.get("background")?.trim() ?? "";
  const initialInterests = params.get("interests")?.trim() ?? "";
  const autorun = params.get("autorun") === "1";

  const [query, setQuery] = useState(initialQuery);
  const [background, setBackground] = useState(initialBackground);
  const [interests, setInterests] = useState(initialInterests);
  const [tone, setTone] = useState<Tone>("warm");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    void apiIsReachable().then((online) => {
      if (!cancelled) {
        setApiOnline(online);
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!autorun || initialQuery.length < 3) {
      return;
    }
    const key = `${initialQuery}|${initialBackground}|${initialInterests}`;
    if (autoRan.has(key)) {
      return;
    }
    autoRan.add(key);
    void runSearch({
      query: initialQuery,
      background: initialBackground,
      interests: initialInterests,
    });
  }, [autorun, initialQuery, initialBackground, initialInterests]);

  async function runSearch(input: { query: string; background: string; interests: string }) {
    const trimmedQuery = input.query.trim();
    if (trimmedQuery.length < 3) {
      setError("Describe who you want to meet in a little more detail.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await searchPeople({
        query: trimmedQuery,
        background: input.background.trim() || undefined,
        interests: input.interests.trim() || undefined,
      });
      setResult(response);
      setApiOnline(true);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Search failed.");
      setApiOnline(false);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-full bg-paper text-ink">
      <header className="border-b border-line">
        <div className="mx-auto flex w-full max-w-3xl items-end justify-between gap-4 px-5 py-5">
          <div>
            <p className="font-serif text-3xl tracking-tight">MeetMind</p>
            <p className="mt-1 max-w-xl text-sm leading-6 text-muted">
              Describe the kind of person you want to meet. MeetMind turns that into a short list
              with match notes, sources, and a draft you can edit.
            </p>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-3xl px-5 py-8">
        <form
          className="rounded-3xl border border-line bg-card p-5"
          onSubmit={(event) => {
            event.preventDefault();
            void runSearch({ query, background, interests });
          }}
        >
          <div className="flex items-center justify-between gap-3">
            <label htmlFor="goal" className="text-sm font-semibold">
              Who do you want to meet?
            </label>
            <button
              type="button"
              className="text-sm font-medium text-accent hover:underline"
              onClick={() => setQuery(SAMPLE_QUERY)}
            >
              Use a sample goal
            </button>
          </div>
          <textarea
            id="goal"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            maxLength={2000}
            rows={5}
            required
            placeholder="I want to meet a product manager working on AI products..."
            className="mt-3 w-full resize-y rounded-2xl border border-line bg-paper px-4 py-3 text-base leading-7 outline-none focus:border-accent"
          />

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="background" className="text-sm font-semibold">
                Your background <span className="font-normal text-muted">(optional)</span>
              </label>
              <textarea
                id="background"
                value={background}
                onChange={(event) => setBackground(event.target.value)}
                maxLength={2000}
                rows={3}
                placeholder="I'm a data scientist exploring product roles."
                className="mt-2 w-full resize-y rounded-2xl border border-line bg-paper px-3 py-2 text-sm leading-6 outline-none focus:border-accent"
              />
            </div>
            <div>
              <label htmlFor="interests" className="text-sm font-semibold">
                Interests <span className="font-normal text-muted">(optional)</span>
              </label>
              <textarea
                id="interests"
                value={interests}
                onChange={(event) => setInterests(event.target.value)}
                maxLength={1000}
                rows={3}
                placeholder="AI, payments, developer tools"
                className="mt-2 w-full resize-y rounded-2xl border border-line bg-paper px-3 py-2 text-sm leading-6 outline-none focus:border-accent"
              />
            </div>
          </div>

          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <label className="flex items-center gap-2 text-sm text-muted">
              Outreach tone
              <select
                value={tone}
                onChange={(event) => setTone(event.target.value as Tone)}
                className="rounded-full border border-line bg-paper px-3 py-1.5 text-ink"
              >
                <option value="warm">Warm</option>
                <option value="direct">Direct</option>
                <option value="curious">Curious</option>
              </select>
            </label>
            <button
              type="submit"
              disabled={loading || query.trim().length < 3}
              className="rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-accent-dark disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Searching…" : "Find people"}
            </button>
          </div>
        </form>

        {error ? (
          <p className="mt-4 rounded-2xl bg-danger-bg px-4 py-3 text-sm text-danger" role="alert">
            {error}
          </p>
        ) : null}

        {loading ? (
          <div className="mt-6 space-y-3" aria-live="polite">
            <p className="text-sm text-muted">Looking through the sample network…</p>
            {[0, 1, 2].map((item) => (
              <div key={item} className="h-36 animate-pulse rounded-3xl bg-line/70" />
            ))}
          </div>
        ) : null}

        {result && !loading ? (
          <section className="mt-6" aria-live="polite">
            <div
              className={`rounded-2xl px-4 py-3 text-sm leading-6 ${
                result.result_source === "mock"
                  ? "bg-warn-bg text-warn"
                  : "bg-paper text-muted"
              }`}
            >
              {result.disclaimer}
            </div>

            <CriteriaSummary criteria={result.criteria} count={result.candidates.length} />

            {result.candidates.length === 0 ? (
              <p className="mt-4 rounded-3xl border border-dashed border-line px-4 py-8 text-center text-sm text-muted">
                No profiles had enough overlap with this goal. Try naming a role, a company, or a
                topic such as AI or product management.
              </p>
            ) : (
              <div className="mt-4 space-y-4">
                {result.candidates.map((candidate) => (
                  <CandidateCard
                    key={candidate.id}
                    candidate={candidate}
                    query={result.query}
                    background={background}
                    interests={interests}
                    tone={tone}
                  />
                ))}
              </div>
            )}
          </section>
        ) : null}
      </main>

      <footer className="mx-auto flex w-full max-w-3xl items-center justify-between px-5 pb-8 text-xs text-muted">
        <p>
          API{" "}
          {apiOnline === null ? "checking…" : apiOnline ? "connected" : "offline"} at {apiBaseUrl()}
        </p>
        <p>Scores are estimates.</p>
      </footer>
    </div>
  );
}

function CriteriaSummary({
  criteria,
  count,
}: {
  criteria: SearchResponse["criteria"];
  count: number;
}) {
  const chips = [
    ...criteria.target_roles.map((role) => `Role: ${role}`),
    ...criteria.target_companies.map((company) => `Company: ${company}`),
    ...criteria.topics.map((topic) => `Topic: ${topic}`),
  ];
  if (criteria.transition_from && criteria.transition_to) {
    chips.push(`Transition: ${criteria.transition_from} → ${criteria.transition_to}`);
  }

  return (
    <div className="mt-4">
      <p className="text-sm text-muted">
        {count === 0
          ? "Nothing to show yet."
          : `${count} ${count === 1 ? "person" : "people"} ranked by estimated overlap.`}
      </p>
      {chips.length > 0 ? (
        <ul className="mt-2 flex flex-wrap gap-2">
          {chips.map((chip) => (
            <li key={chip} className="rounded-full border border-line bg-card px-3 py-1 text-xs">
              {chip}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
