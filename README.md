Smart Canteen — Local Frontend + Demo Backend

What's included
- Frontend: static HTML/CSS/JS files (index.html, register.html, login.html, user_dashboard.html, payment.html, etc.)
- Demo backend: `backend/app.py` (Flask) with `/api/checkout` endpoint

Changes made
- Form validation: stricter email validation (disallows numeric-only local-part) and password rules (min 8 chars, 1 uppercase, 1 special) implemented and used in registration.
- Menu/cart: quantity controls synced with cart; improved add/update/remove logic and UI sync.
- Payment: client attempts POST to `/api/checkout` (server stub) with fallback to local simulation.
- Backend: minimal Flask app + Postgres attempt; default DB: `canteen`, password `Kavin04`.
- Minor UI enhancements: notification styles and better form hints.

Font
- This project references a custom font named Aleoverasans. To apply the font locally, place an `Aleoverasans.woff2` file in a `fonts` folder at project root (`/fonts/Aleoverasans.woff2`). If you don't have the font file, the site will fall back to system fonts.

Run frontend
- Open the HTML files in a browser (e.g., open `index.html`). For full checkout integration run the backend.

Run backend
- See [backend/README.md](backend/README.md) for steps.
