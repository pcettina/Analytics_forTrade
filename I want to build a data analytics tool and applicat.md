<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# I want to build a data analytics tool and application interface to pull baseball stats for all players/teams in the MLB for generating a prediction market tracker and trader I want you to research all necessary analytics and analysis packages I will need as well as prefferred language and set up for submitting in a project file to an agentic coding application to build the full tool/application

You can build this as a full TypeScript/Node monorepo with a Next.js frontend, a NestJS (or Fastify) API, Postgres + Prisma for storage, and a TypeScript analytics package using Danfo.js, TensorFlow.js, and simple-statistics for modeling MLB player props and season futures on top of public MLB data (primarily the MLB Stats API and Baseball Savant/FanGraphs exports). The outline below is designed so you can hand it directly to an agentic coding system to scaffold the project.[^1][^2][^3][^4]

***

## Core stack and language

- Language/runtime
    - TypeScript on Node 20+ for backend and analytics.[^5]
    - Next.js 14+ (App Router) for the web UI in TypeScript.[^6]
- Backend framework
    - NestJS for strongly structured modular services (ingestion, analytics, markets, trading), DI, and OpenAPI generation.[^7]
    - Alternative: Fastify with a modular folder structure if you want something lighter; both are well supported in TS.[^8]
- Database and ORM
    - PostgreSQL as the primary store for players, games, stats, markets, and trades.[^9]
    - Prisma ORM for type-safe DB access and schema migrations in TypeScript.[^10]
- Caching/queueing
    - Redis for caching high-traffic endpoints (current lines, today’s projections) and job queues.
    - BullMQ (Redis-based) for scheduled ingestion and backfills.
- Packaging and repo layout
    - Monorepo with pnpm or yarn workspaces: `apps/api`, `apps/web`, `packages/analytics`, `packages/core-types`.

***

## MLB data sources and ingestion

- MLB Stats API (statsapi.mlb.com)
    - Unofficial JSON API used widely for schedules, rosters, player IDs, and basic boxscore stats.
    - Good for: game schedule, daily box scores, season-level splits (some), roster/transaction context.
- Baseball Savant / Statcast
    - Public CSV and JSON endpoints (often via query URLs), with pitch- and batted-ball-level data.
    - Good for: advanced features (hard-hit rate, launch angle, xwOBA, etc.), which matter for player prop modeling.
- FanGraphs exports
    - CSV exports for season and game logs, including plate discipline, pitch-type usage, and projection systems.[^1]
    - Good for: backfilling historical stats and park factors if ToS and scraping rules are respected.
- Odds / lines (optional if you define your own internal markets)
    - If you eventually need reference lines, you can use free- or freemium-odds APIs (e.g., The Odds API or similar) subject to their ToS, or manually entered lines.
- Node ingestion packages and patterns
    - HTTP client: `undici` or `axios` for requests.
    - Validation: `zod` schemas for each external payload (MLB Stats API game, player, boxscore, etc.).
    - Scheduling: `node-cron` or BullMQ repeatable jobs for daily pulls and overnight historical sync.

**Ingestion workflow:**

1. Seed historical data: backfill several seasons of games and player stats from FanGraphs CSV and MLB Stats API.
2. Nightly job: pull previous day’s final box scores and update `PlayerGameStats`, `Game`, and derived season aggregates.
3. Pre-game job: on a short interval (e.g., every 10–15 minutes), pull today’s probable pitchers, lineups, and any available “live” updates you’ll use for props (e.g., updated starting lineups, last-minute scratches).

***

## Analytics and modeling libraries in TypeScript/Node

### Tabular and numerical foundations

- Danfo.js
    - DataFrame/Series library modeled on pandas for JS/TS, with groupby, rolling windows, joins, and CSV/JSON IO.[^2]
    - Use for feature engineering (rolling averages, splits, park adjustments) and for preparing matrices for models.
- simple-statistics
    - Provides descriptive stats, distributions, correlation, linear regression, and quantile functions in JS.[^4]
    - Useful for baseline models, calibration metrics, and computing summary stats for props.
- mathjs or ml-matrix
    - mathjs for general numerical operations and random draws; ml-matrix for matrix algebra and decompositions.


### ML / forecasting in JS

- TensorFlow.js
    - Neural network and linear-model library in JS, with CPU and WebGL backends.[^3]
    - Use for: generalized linear models, shallow feed-forward nets, or sequence models (e.g., RNN/1D CNN) for player performance time-series.
- ml.js family
    - A collection of ML algorithms (e.g., regressions, naive Bayes, random forests) implemented in JS.
    - Use for: tree-based models on engineered features if you want to stay fully in TS.
- Time-series
    - JS ecosystem is weaker than Python here; a pragmatic approach is:
        - Engineer time-dependent features in Danfo (rolling windows, exponential moving averages, recency weights).[^2]
        - Apply general-purpose models (GLMs, random forests, or TF.js networks) to those features rather than strict ARIMA-style models.


### Simulation and risk/edge analytics

- Use `mathjs` / `ml-matrix` plus your own Monte Carlo simulator:
    - Draw plate-appearance outcomes based on modeled probabilities (strikeout, walk, hit types, etc.).
    - Simulate many games or PA sequences to estimate distribution of stat lines vs a prop line and compute the probability of going over/under.
- Randomness and reproducibility
    - `seedrandom` (or similar) to seed RNG for reproducible simulations.

**If you later relax the “pure TS” constraint**, an additional analytics service in Python (scikit-learn, xgboost, statsmodels) behind an internal HTTP/gRPC interface is the most efficient way to upgrade modeling power without changing the rest of the stack.

***

## Domain modeling and database schema

Below is a minimal relational schema you can hand to the agent system; it assumes PostgreSQL with Prisma, but the conceptual model is OR-agnostic.[^9][^10]

### Core entities

| Entity | Purpose | Key fields (examples) |
| :-- | :-- | :-- |
| `Team` | MLB team metadata | `id`, `mlb_team_id`, `name`, `abbrev`, `league`, `division` |
| `Player` | Player master record | `id`, `mlb_player_id`, `name`, `handedness_bat`, `handedness_throw`, `team_id` |
| `Game` | Game metadata and status | `id`, `mlb_game_id`, `date`, `home_team_id`, `away_team_id`, `status`, `venue_id` |
| `PlayerGameStats` | Per-player per-game boxscore | `id`, `player_id`, `game_id`, `pa`, `ab`, `hits`, `hr`, `bb`, `k`, `ip`, `er`, etc. |
| `SeasonStats` | Aggregated season stats by player and season | `id`, `player_id`, `season`, `team_id`, batting/pitching aggregates |
| `ProjectionRun` | Versioned projection runs | `id`, `created_at`, `model_version`, `assumptions_json` |
| `PlayerProjection` | Projected stats per player per game or per season | `id`, `projection_run_id`, `player_id`, `game_id?`, `season?`, metric fields (e.g., `proj_hits`, `proj_ks`) |
| `Market` | Prediction market contract definition | `id`, `scope` (game/season), `type` (prop/future), `player_id?`, `game_id?`, `line`, `side` (over/under), `settlement_rule` |
| `MarketPrice` | Time-series of quoted prices/odds for each market | `id`, `market_id`, `timestamp`, `implied_prob`, `bid`, `ask`, `source` |
| `Order` / `Trade` | User actions and fills if you build an internal exchange/trader | `id`, `user_id`, `market_id`, `side`, `price`, `size`, `status`, `filled_size` |
| `User` | User accounts (optional if you only run this as a research tool) | `id`, `email`, `hashed_password`, roles, etc. |

This schema supports both game-level props (e.g., “O/U 6.5 strikeouts for a specific pitcher in a specific game”) and season-long futures (“Over 35.5 home runs for a player this season”), while keeping projections versioned via `ProjectionRun`.[^10][^9]

***

## Application architecture and project layout

Use a monorepo structure that an agentic builder can map directly to apps and packages:

```text
.
├─ apps/
│  ├─ api/          # NestJS or Fastify backend
│  └─ web/          # Next.js frontend
├─ packages/
│  ├─ analytics/    # Pure TS analytics + modeling
│  ├─ core-types/   # Shared types and validation (zod)
│  └─ ui/           # Reusable React components, if desired
└─ infra/
   └─ docker/       # Dockerfiles, docker-compose, k8s manifests
```


### `apps/api` (backend)

- Modules (NestJS terms) / feature folders:
    - `mlb-ingest`: fetch MLB Stats API, Baseball Savant, FanGraphs CSV, map to internal schema.[^1]
    - `stats`: serve canonical stats and projections (REST/GraphQL endpoints).
    - `markets`: define and manage prediction markets, expose current markets and prices.
    - `trading`: accept orders, perform matching (if you build an exchange-like trader).
    - `auth`: user accounts, API keys.
    - `jobs`: BullMQ processors for ingestion and model runs.
- Patterns:
    - DTOs + zod schemas for request/response validation.
    - Prisma-based repositories for each entity.
    - Config module that wires env vars: DB/Redis URLs, external API keys, etc.


### `apps/web` (frontend)

- Next.js with React Query (TanStack Query) or SWR for data fetching.
- Pages / routes:
    - `/players`: searchable list of players with projections and recent stats.
    - `/games`: today’s games, props for each starting pitcher/hitter.
    - `/markets`: current markets with price charts and projected edges.
    - `/portfolio` (if multi-user): positions, PnL, trade history.
- Visualization:
    - `recharts`, `nivo`, or `visx` for time-series and distribution plots (e.g., distribution of projected Ks vs line).


### `packages/analytics` (TS analytics library)

Organize as a pure-function library with no framework dependencies:

- `etl/`
    - Transformers mapping raw MLB Stats API / Savant / FanGraphs payloads into normalized tables and features.
- `features/`
    - Rolling stats (last N games, last N days).
    - Platoon splits (vs LHP/RHP), home/away, park factors.
    - Exponential recency weights to give more importance to recent performance.
- `models/`
    - Prop models for each stat type (Ks, hits, HRs, etc.), built with simple-statistics, Danfo, TensorFlow.js, or ml.js.[^3][^4][^2]
    - Outputs parameters for distributions (e.g., Poisson rate for Ks, distribution over hits).
- `simulation/`
    - Monte Carlo engine that, given distribution parameters and a market line, estimates:
        - $P(\text{stat} \ge L)$ and $P(\text{stat} \le L)$ for O/U.
        - Expected value at given prices or odds.
- `evaluation/`
    - Backtesting tools to compare projected vs realized outcomes, Brier scores, log loss, calibration plots.

***

## Key NPM dependencies (grouped)

You can feed this directly into an agentic tool as dependency requirements.[^5][^6][^7][^8][^10]

- Core tooling
    - `typescript`, `ts-node`, `tsx`
    - `eslint`, `prettier`, `jest` or `vitest`
    - `dotenv`, `cross-env`
- Backend (API)
    - `@nestjs/core`, `@nestjs/common`, `@nestjs/config`, `@nestjs/schedule`, `@nestjs/swagger` (if NestJS)
    - or `fastify`, `@fastify/swagger`
    - `@prisma/client`, `prisma`
    - `pg` (Postgres driver)
    - `ioredis` or `redis` (client)
    - `bullmq` (jobs)
    - `undici` or `axios` (HTTP)
    - `zod` (validation)
    - `pino` or `winston` (logging)
- Frontend (web)
    - `next`, `react`, `react-dom`
    - `@tanstack/react-query` or `swr`
    - `recharts` / `nivo` / `visx` for charts
- Analytics / modeling
    - `danfojs-node` (server-side Danfo)[^2]
    - `simple-statistics`[^4]
    - `mathjs` or `ml-matrix`
    - `@tensorflow/tfjs-node` (if you use TF.js models)[^3]
    - `ml` (ml.js algorithms) or more focused `ml-regression`, `ml-random-forest`
    - `seedrandom` (RNG seeding)

***

## Analytics and modeling workflow (for player props and futures)

- Data preparation
    - Build unified player IDs and align MLB Stats API IDs with Savant/FanGraphs where needed.[^1]
    - For each player, construct robust time-series of relevant stats (e.g., strikeout rate, pitch count, innings per start, hard-hit rate, plate appearances).
- Feature engineering
    - Rolling windows (3, 5, 10-game) with recency weighting.
    - Opponent strength features (team offense/defense, K% allowed, park factors).
    - Contextual features: home/away, temperature, lineup position, rest days.
- Modeling
    - For game-level props, model per-game stat distribution:
        - Example: Ks as Poisson with rate parameter estimated by regression (linear/GLM) on engineered features.
        - Example: Hits as something close to binomial or negative binomial, built from per-PA hit probability and expected PA count.
    - For season-long futures, model cumulative totals as sums of projected game-level distributions with injury/playing-time assumptions.
- Simulation and edge computation
    - Run Monte Carlo draws to approximate the distribution of totals vs the prop line.
    - Compute probability of over/under and compare to market-implied probability from odds to derive edge and expected value.
- Monitoring
    - Store realized outcomes per projection run and compute calibration and profitability metrics to refine models over time.

***

## Spec template for your agentic coding application

You can paste/edit the following into your agent system as a project spec:

```markdown
# Project: MLB Player Prop & Futures Prediction Market Tracker

## Goals
- Ingest free/public MLB data (MLB Stats API, Baseball Savant, FanGraphs CSVs).
- Build a TypeScript/Node-based analytics engine to project player-level props
  (e.g., strikeouts, hits) and season-long futures.
- Expose a web UI and API to track projected edges vs market lines and simulate trades.

## Tech Stack
- Language: TypeScript
- Runtime: Node.js 20+
- Backend: NestJS (or Fastify) REST API
- Frontend: Next.js (React) web app
- Database: PostgreSQL with Prisma ORM
- Cache/Queue: Redis + BullMQ
- Analytics: danfojs-node, simple-statistics, mathjs/ml-matrix, @tensorflow/tfjs-node (optional),
  ml.js family, seedrandom

## Monorepo Structure
- apps/api: Backend API server
- apps/web: Next.js frontend
- packages/analytics: Pure TypeScript analytics and modeling library
- packages/core-types: Shared domain types and zod schemas
- infra: Docker, docker-compose, deployment scripts

## Domain Model (Database)
Implement entities:
- Team, Player, Game, PlayerGameStats, SeasonStats
- ProjectionRun, PlayerProjection
- Market, MarketPrice
- User, Order, Trade

## API Requirements
- /api/players
  - List/search players with current season stats and upcoming game projections.
- /api/games
  - Today’s and upcoming games with associated player props.
- /api/markets
  - List markets (props and futures) with current prices and model-projected edges.
- /api/projections
  - Raw projections and distributions per player/game/season for internal and UI use.
- /api/trades (optional)
  - Place and list orders, trades, and positions.

## Ingestion & Jobs
- Job to backfill historical seasons from FanGraphs CSV and MLB Stats API.
- Daily job to ingest prior day’s final boxscores (PlayerGameStats).
- Pre-game periodic job to refresh today’s games, lineups, and projected props.
- Jobs trigger analytics package to recompute projections and write to PlayerProjection.

## Analytics Package Design (packages/analytics)
- etl/: Transform raw MLB Stats API / Savant / FanGraphs data into normalized tables.
- features/: Compute rolling stats, splits, park factors, opponent strength features.
- models/: Fit prop/future models using simple-statistics, danfojs-node, tfjs/ml.js as appropriate.
- simulation/: Monte Carlo utilities to estimate probabilities vs a given line and compute edge.
- evaluation/: Backtesting utilities (Brier score, calibration, PnL).

## Frontend Requirements (apps/web)
- Player pages: historical stats, upcoming projections, prop markets.
- Game dashboard: per-game props with probabilities and implied edges.
- Markets dashboard: sortable/filterable table of all markets with implied vs projected probabilities.
- (Optional) Trader UI: submit orders, see positions and PnL over time.

## Non-Functional Requirements
- Type-safe end-to-end with shared types between backend, frontend, and analytics.
- Config via environment variables for DB, Redis, external APIs.
- Basic auth (JWT or session) to protect trading endpoints if implemented.
- Logging and simple metrics for ingestion and model runs.
```

This gives an agentic coding system a clear blueprint of the stack, packages, data model, and modules needed to build your MLB prediction market tracker in a full TypeScript/Node environment while relying only on public MLB data sources.
<span style="display:none">[^11][^12]</span>

<div align="center">⁂</div>

[^1]: interests.spreadsheets_excel

[^2]: interests.medical_sports_history.nba_injuries

[^3]: https://www.perplexity.ai/search/e535aab4-011f-4b09-b67e-c4223a6bacde

[^4]: https://www.perplexity.ai/search/ce605a3a-8b1f-4848-9564-247c839d7a47

[^5]: https://www.perplexity.ai/search/7098562e-97fc-44ab-84f9-7e4d3ca6dc1b

[^6]: https://www.perplexity.ai/search/a018303b-05cf-4701-ab80-dfe5110890cc

[^7]: https://www.perplexity.ai/search/f0dada02-bd3e-4cfe-9774-fca869687538

[^8]: https://www.perplexity.ai/search/65f96e70-1bec-47d3-8082-f52d984b3eab

[^9]: https://www.perplexity.ai/search/35a216e9-0ea8-4246-acd9-100892558baf

[^10]: https://www.perplexity.ai/search/9657d282-c7c7-4635-83f9-a8bdb19dee86

[^11]: https://www.perplexity.ai/search/deefbdc6-e57f-47a0-adbc-dd050808a786

[^12]: https://www.perplexity.ai/search/b20e3120-bc32-4241-93a3-63f9a51e8972

