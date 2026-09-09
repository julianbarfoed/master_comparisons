# Audio frontend

React/Vite project skeleton for the audio interface.

See the root [README](../README.md) and [agent workflow](../docs/workflow.md).

## Layout

- `src/App.tsx` — application shell
- `src/lib/api.ts` — API-client boundary
- `src/lib/supabase.ts` — authentication-provider boundary
- `src/styles.css` — base application styles

## Run locally

```sh
npm ci
npm run dev
```

The UI is static: no authentication, API calls, upload handling, playback, or data state has been implemented.

Run `npm test` for Vitest/Testing Library tests, `npm run typecheck` for TypeScript,
and `npm run build` for typechecking plus a production build. `npm run test:watch`
starts interactive tests. `make check-frontend` at the root runs tests and the build.

The Supabase module is an unused scaffold placeholder, not a provider decision.
The API client and authentication flow are defined when assigning frontend work.
`VITE_API_URL` in `.env.example` suggests the local backend origin.
