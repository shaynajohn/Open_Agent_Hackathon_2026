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

Open `http://localhost:3010`. The sample goal button fills the Stripe / product-manager example.

`NEXT_PUBLIC_API_BASE_URL` defaults to `http://localhost:8000`. The backend allows that origin through `CORS_ORIGINS`.

## Chrome extension

The popup has no host permissions and no content scripts. It does not read the current tab.

```bash
cd extension
npm install
npm run build
```

Then, in Chrome, open `chrome://extensions`, enable Developer mode, choose **Load unpacked**, and select the `extension/` directory.

`WEB_APP_URL` in `extension/src/popup.ts` is `http://localhost:3010`. Rebuild after changing it. **Search in MeetMind** opens the app with the goal filled in and runs the search. **Open the app** opens it without starting a search.

## Environment

| Variable | Where | Purpose |
| --- | --- | --- |
| `SEARCH_PROVIDER` | `backend/.env` | `mock` (default), `exa`, or `tavily` |
| `LLM_PROVIDER` | `backend/.env` | `mock` (default), `openai`, or `nightshift` |
| `NIGHTSHIFT_API_KEY` | `backend/.env` | Runtime token. NVIDIA keys stay in Nightshift |
| `NIGHTSHIFT_BASE_URL` | `backend/.env` | Defaults to `http://127.0.0.1:8088/v1` |
| `ZETARIS_REST_URL` | `backend/.env` | API base ending in `/api/v1.0` |
| `ZETARIS_BASE_URL` | `backend/.env` | Gateway origin, when the cluster has no public REST port |
| `ZETARIS_ORG_ID` | `backend/.env` | Numeric organisation ID |
| `ZETARIS_API_KEY` | `backend/.env` | Token from Management → API Tokens |
| `EXA_API_KEY` | `backend/.env` | Only for `SEARCH_PROVIDER=exa` |
| `TAVILY_API_KEY` | `backend/.env` | Only for `SEARCH_PROVIDER=tavily` |
| `OPENAI_API_KEY` | `backend/.env` | Only when a route starts calling `llm.py` |
| `OPENAI_MODEL` | `backend/.env` | Defaults to `gpt-4o-mini` |
| `CORS_ORIGINS` | `backend/.env` | Local frontend origins |
| `NEXT_PUBLIC_API_BASE_URL` | `frontend/.env.local` | Backend origin |

Root `.env.example` lists the same variables. Do not commit `.env` or `.env.local`.

## Zetaris on AWS Free Tier

MeetMind stays on port 3010. The MeetMind API stays on port 8000. Nightshift stays on port 8088. Port 8888 is only the local Docker REST port. An AWS cluster has its own hostname.

Use a new AWS Free plan account so the cluster draws on credits. In Zetaris testing, a Mini cluster left running for about a week used roughly $80. Suspend or delete it when you are done.

1. Sign in to Zetaris Cloud Gateway and AWS.
2. Compute → Credentials → Add AWS Account → Quickstart. Region `us-west-1`. Launch the stack, wait for `CREATE_COMPLETE`, then Verify.
3. Compute → Clusters → Create Cluster. Choose the verified account, size Mini, and wait until the cluster is Active. Provisioning takes about 30 minutes.
4. Open the cluster Overview, then the Sign-in URL. Copy the administrator password from Organisations on that page. Sign in to the Gateway.
5. Management → API Tokens → create a key. Management → Organisation → copy the numeric ID.
6. Put those values in `backend/.env` only:

```bash
ZETARIS_ORG_ID=the-numeric-id
ZETARIS_API_KEY=the-token
# Prefer the cluster API base when the Access page shows one.
ZETARIS_REST_URL=https://your-cluster-host/api/v1.0
# Otherwise set the Gateway sign-in origin and leave REST at the local default.
ZETARIS_BASE_URL=https://your-gateway-host
```

7. Install Nightshift, connect an NVIDIA model in its Providers tab, and paste the runtime token into `NIGHTSHIFT_API_KEY`. Do not use `rt-local`.
8. From `backend/`, with the virtualenv active:

```bash
uvicorn app.main:app --reload --port 8000
curl http://127.0.0.1:8000/api/integrations
```

`zetaris.ok` is true when `SELECT 1` returns 1. `nightshift.ok` is true when one completion returns text. The model id is in that response and in `backend/logs/model-calls.jsonl`. Search results stay on the sample profiles until a later change reads Zetaris.

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
