# Frontend

Next.js (App Router) con TypeScript estricto y Tailwind. El navegador solo habla con las rutas
`/api` de Next (patrón BFF): `/api/auth/login` guarda el JWT en una cookie httpOnly y
`/api/backend/[...ruta]` reenvía cada petición al backend con ese token.

```
cp .env.example .env.local   # BACKEND_URL apunta al backend FastAPI
npm install
npm run dev                  # http://localhost:3000
npm run lint && npm run typecheck && npm run build
npm run e2e                  # levanta backend y frontend locales; E2E_BASE_URL para producción
```
