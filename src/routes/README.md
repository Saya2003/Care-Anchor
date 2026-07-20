# Routes

TanStack Start uses **file-based routing**. Every `.tsx` file in this directory
defines a route. Do **not** create `src/pages/`, `src/routes/_app/index.tsx`, or
`app/layout.tsx` — those are Next.js / Remix conventions. The only root layout
is `src/routes/__root.tsx`.

## Conventions

| File | URL |
| --- | --- |
| `index.tsx` | `/` |
| `about.tsx` | `/about` |
| `users/index.tsx` | `/users` |
| `users/$id.tsx` | `/users/:id` (dynamic — bare `$`, no curly braces) |
| `posts/{-$category}.tsx` | `/posts/:category?` (optional segment) |
| `files/$.tsx` | `/files/*` (splat — read via `_splat` param, never `*`) |
| `_layout.tsx` | layout route (renders children via `<Outlet />`) |
| `__root.tsx` | app shell — wraps every page; preserve `<Outlet />` |

`routeTree.gen.ts` is auto-generated. Don't edit it by hand.


## CareAnchor Routes

### Public Routes
- `/` - Landing page (redirects to `/dashboard` if authenticated)
- `/auth` - Sign in and sign up page

### Authenticated Routes (Protected)
All routes under `_authenticated/` require user authentication:

- `/dashboard` - Main dashboard with overview and quick actions
- `/app` - Chat interface with CareAnchor agent
- `/settings` - User settings and preferences
- `/logout` - Sign out handler (redirects to `/`)

### Authentication Flow

1. User visits `/auth` and signs in or signs up
2. After successful authentication, user is redirected to `/dashboard`
3. All authenticated routes check for valid session via `_authenticated/route.tsx`
4. If session is invalid, user is redirected back to `/auth`

### Key Features

- **Auto-redirect**: Authenticated users visiting `/` are automatically redirected to `/dashboard`
- **Protected routes**: All routes under `_authenticated/` require authentication
- **Sign out**: `/logout` route handles sign out and redirects to landing page
- **Navigation**: Consistent navigation across dashboard, chat, and settings pages
