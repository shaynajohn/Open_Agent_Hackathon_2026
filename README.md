# MeetMind

MeetMind helps people find someone worth meeting. A user describes a networking goal, and the app returns a short list of candidates with estimated match notes, source links, and a draft outreach note.

This repository is the initial hackathon scaffold. Search, ranking, and outreach run end to end on **fictional sample profiles**. No API keys are required.

MeetMind does not scrape LinkedIn, automate LinkedIn, or inject UI into LinkedIn. Discover people from public sources that allow the intended use, such as company team pages, conference bios, interviews, and articles. A LinkedIn URL may be shown only after it is verified from a source like that.

## Architecture

```text
Chrome extension  →  Next.js web app  →  FastAPI
                                         ├─ intent parsing
                                         ├─ search provider (mock, Exa, or Tavily)
                                         ├─ candidate extraction and dedupe
                                         ├─ ranking
                                         └─ outreach draft
```

The extension only opens the web app. API keys stay in the backend environment.

| Path | Responsibility |
| --- | --- |
| `frontend/` | Search form, candidate cards, outreach drafts |
| `backend/app/services/intent.py` | Turn a sentence into roles, companies, and topics |
| `backend/app/services/search/` | Swappable web search. Default is local sample data |
| `backend/app/services/extraction.py` | Build candidates from retrieved documents |
| `backend/app/services/ranking.py` | Estimate overlap and explain it |
| `backend/app/services/outreach.py` | Draft a note from known fields |
| `backend/app/services/llm.py` | OpenAI-compatible client, not used by the routes yet |
| `extension/` | Manifest V3 popup |

There is no database. Add Supabase or Postgres later behind the service functions without changing the API shape.

## API

- `GET /health` — status check
- `POST /api/search` — `{ query, background?, interests? }` → criteria and candidates
- `POST /api/outreach` — `{ candidate, query, background?, interests?, tone? }` → subject and message

Interactive docs: `http://localhost:8000/docs`

Match scores are estimates from 0 to 100, not facts. Reasons are limited to fields that were actually present. The mock provider labels its people as fictional.

## Prerequisites

- Node.js 22+
- Python 3.12+
- Chrome, for the extension

## Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Tests:

```bash
cd backend
source .venv/bin/activate
pytest
```

## Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`. The sample goal button fills the Stripe / product-manager example.

`NEXT_PUBLIC_API_BASE_URL` defaults to `http://localhost:8000`. The backend allows that origin through `CORS_ORIGINS`.

## Chrome extension

The popup has no host permissions and no content scripts. It does not read the current tab.

```bash
cd extension
npm install
npm run build
```

Then, in Chrome, open `chrome://extensions`, enable Developer mode, choose **Load unpacked**, and select the `extension/` directory.

`WEB_APP_URL` in `extension/src/popup.ts` defaults to `http://localhost:3000`. Change it and rebuild when the app is hosted somewhere else. **Search in MeetMind** opens the app with the goal filled in and runs the search. **Open the app** opens it without starting a search.

## Environment

| Variable | Where | Purpose |
| --- | --- | --- |
| `SEARCH_PROVIDER` | `backend/.env` | `mock` (default), `exa`, or `tavily` |
| `LLM_PROVIDER` | `backend/.env` | `mock` (default) or `openai` |
| `EXA_API_KEY` | `backend/.env` | Only for `SEARCH_PROVIDER=exa` |
| `TAVILY_API_KEY` | `backend/.env` | Only for `SEARCH_PROVIDER=tavily` |
| `OPENAI_API_KEY` | `backend/.env` | Only when a route starts calling `llm.py` |
| `OPENAI_MODEL` | `backend/.env` | Defaults to `gpt-4o-mini` |
| `CORS_ORIGINS` | `backend/.env` | Local frontend origins |
| `NEXT_PUBLIC_API_BASE_URL` | `frontend/.env.local` | Backend origin |

Root `.env.example` lists the same variables. Do not commit `.env` or `.env.local`.

## What is mock, and what to build next

Running today without credentials:

- **Intent parsing** uses keyword rules in `intent.py`. It is good enough for the demo query and easy to replace.
- **Search** returns eight fictional profiles from `backend/app/fixtures/mock_profiles.py`. Source links point at `example.com` placeholders. None of them include a LinkedIn URL.
- **Ranking** scores overlap of role, company, topics, career transition, and interests. If a requested company is not on the profile, the reason says so instead of implying they work there.
- **Outreach** fills a template from the candidate fields and the user's own words.
- **Exa and Tavily clients** can already request public pages and exclude `linkedin.com`. They are not used unless you opt in. Extraction still refuses to invent a person from unstructured page text, so those providers currently return documents and an empty candidate list.
- **`llm.py`** can call an OpenAI-compatible chat endpoint. The search and outreach routes do not call it yet.

Suggested next steps, in order:

1. Replace `parse_intent` with a call that returns the same `SearchCriteria` shape.
2. Teach `extract_candidates` to read Exa or Tavily documents and emit only fields supported by a source URL. Leave `linkedin_url` empty unless a permitted page verifies it.
3. Replace `generate_outreach` with a prompt that may use only the submitted candidate and user context.
4. Add persistence later. The route handlers do not need to know which database you pick.
