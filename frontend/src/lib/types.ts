export type SearchRequest = {
  query: string;
  background?: string;
  interests?: string;
};

export type SearchCriteria = {
  raw_query: string;
  target_roles: string[];
  target_companies: string[];
  topics: string[];
  background?: string | null;
  interests: string[];
  transition_from?: string | null;
  transition_to?: string | null;
};

export type Candidate = {
  id: string;
  name: string;
  role: string;
  company: string;
  relevant_experience: string;
  match_score: number;
  match_reasons: string[];
  source_urls: string[];
  linkedin_url?: string;
  outreach_draft?: string;
};

export type SearchResponse = {
  query: string;
  criteria: SearchCriteria;
  candidates: Candidate[];
  result_source: "mock" | "web";
  sources_retrieved: number;
  disclaimer: string;
};

export type OutreachRequest = {
  candidate: Candidate;
  query: string;
  background?: string;
  interests?: string;
  tone?: "warm" | "direct" | "curious";
};

export type OutreachResponse = {
  candidate_name: string;
  subject: string;
  message: string;
  result_source: "mock" | "llm";
  disclaimer: string;
};
