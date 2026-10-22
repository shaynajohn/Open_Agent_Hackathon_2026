"use client";

import { useState } from "react";
import { createOutreach } from "@/lib/api";
import type { Candidate, OutreachResponse } from "@/lib/types";

type CandidateCardProps = {
  candidate: Candidate;
  query: string;
  background: string;
  interests: string;
  tone: "warm" | "direct" | "curious";
};

export function CandidateCard({
  candidate,
  query,
  background,
  interests,
  tone,
}: CandidateCardProps) {
  const [draft, setDraft] = useState<OutreachResponse | null>(null);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onOutreach() {
    if (draft) {
      setOpen((current) => !current);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await createOutreach({
        candidate,
        query,
        background: background.trim() || undefined,
        interests: interests.trim() || undefined,
        tone,
      });
      setDraft(response);
      setOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not draft outreach.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <article className="rounded-3xl border border-line bg-card p-5 shadow-[0_1px_0_rgba(28,25,21,0.04)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-serif text-2xl tracking-tight text-ink">{candidate.name}</h3>
          <p className="mt-1 text-sm text-muted">
            {candidate.role} at {candidate.company}
          </p>
        </div>
        <p
          className="shrink-0 rounded-full bg-paper px-3 py-1 text-sm font-semibold text-accent"
          title="Estimated alignment for ranking. This is not an objective score."
        >
          Est. {candidate.match_score}
        </p>
      </div>

      <p className="mt-4 text-sm leading-6 text-ink">{candidate.relevant_experience}</p>

      <div className="mt-4">
        <h4 className="text-xs font-semibold tracking-wide text-muted uppercase">
          Why this might fit
        </h4>
        <ul className="mt-2 space-y-1.5 text-sm leading-6 text-ink">
          {candidate.match_reasons.map((reason) => (
            <li key={reason} className="flex gap-2">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
              <span>{reason}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-sm">
        {candidate.source_urls.map((url) => (
          <a
            key={url}
            href={url}
            target="_blank"
            rel="noreferrer"
            title={url}
            className="text-accent underline decoration-accent/30 underline-offset-4 hover:decoration-accent"
          >
            {sourceHost(url)}
          </a>
        ))}
        {candidate.linkedin_url ? (
          <a
            href={candidate.linkedin_url}
            target="_blank"
            rel="noreferrer"
            className="text-accent underline decoration-accent/30 underline-offset-4 hover:decoration-accent"
          >
            LinkedIn
          </a>
        ) : null}
      </div>

      <div className="mt-5">
        <button
          type="button"
          onClick={() => void onOutreach()}
          disabled={loading}
          className="rounded-full bg-ink px-4 py-2 text-sm font-semibold text-card transition hover:bg-accent disabled:cursor-wait disabled:opacity-70"
        >
          {loading ? "Drafting…" : draft ? (open ? "Hide outreach draft" : "View outreach draft") : "Draft outreach"}
        </button>
        {error ? (
          <p className="mt-3 text-sm text-danger" role="alert">
            {error}
          </p>
        ) : null}
        {draft && open ? (
          <div className="mt-4 rounded-2xl bg-paper p-4">
            <p className="text-xs font-semibold tracking-wide text-muted uppercase">Subject</p>
            <p className="mt-1 text-sm font-medium">{draft.subject}</p>
            <p className="mt-4 text-sm leading-6 whitespace-pre-wrap">{draft.message}</p>
            <p className="mt-4 text-xs leading-5 text-muted">{draft.disclaimer}</p>
          </div>
        ) : null}
      </div>
    </article>
  );
}

function sourceHost(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "Source";
  }
}
