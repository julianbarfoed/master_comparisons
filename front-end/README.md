# Audio frontend

React/Vite project skeleton for the audio interface.

See the root [README](../README.md), [API contract](../docs/api.md), and
[frontend task](../docs/tasks/frontend.md).

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

The first milestone uses the Python API without authentication. The Supabase module
is an unused placeholder for later work. `VITE_API_URL` defaults to
`http://localhost:8000` in the contract; the frontend agent implements the client.
