# MOHRE Employee Registry — GGHL

Browse MOHRE "List of Employees" PDFs with slicers, permit-expiry tracking,
and Excel export. **No Python or Git commands needed on your PC** — only the
GitHub Desktop app. PDF parsing happens automatically on GitHub's servers.

## Files

| File | Purpose |
|---|---|
| `index.html` | The app (this is what GitHub Pages serves). |
| `data.js` | The extracted data — written automatically by GitHub. |
| `parse_pdfs.py` | The parser GitHub runs in the cloud. Don't touch. |
| `.github/workflows/update-data.yml` | Tells GitHub when to run the parser. |
| `*.pdf` | Your MOHRE PDFs — just drop them in this folder. |

## One-time setup

1. Install **GitHub Desktop** → https://desktop.github.com → sign in.
2. GitHub Desktop → File → **New repository**
   - Name: `mohre-registry`
   - Local path: `D:\` (it creates `D:\mohre-registry` — or point it at D:\MOLdata's parent)
3. Copy ALL files from this zip (including the hidden `.github` folder)
   into that folder, plus your PDF files.
4. GitHub Desktop → **Publish repository** (untick "keep private" if you
   want free GitHub Pages — see privacy note below).
5. On github.com → your repo → **Settings → Pages** →
   Deploy from a branch → `main` / `(root)` → Save.
6. On github.com → your repo → **Actions** tab → enable workflows if asked.

Your app link: `https://<your-username>.github.io/mohre-registry/`

## Updating the data (routine — 3 clicks, no commands)

1. Copy the new MOHRE PDF into the folder (delete old ones you don't want).
2. Open **GitHub Desktop** — it shows the changed files automatically.
3. Type anything in "Summary" (e.g. *new PDF*) → **Commit to main** → **Push origin**.

That's it. GitHub runs the parser in the cloud (~1–2 minutes), updates
`data.js`, and the live app refreshes itself. You can watch progress in the
repo's **Actions** tab.

To see the update locally too, click **Fetch origin → Pull** in GitHub
Desktop afterwards.

## ⚠️ Privacy note

These lists contain passport numbers. Free GitHub Pages requires a PUBLIC
repo, meaning anyone with the link can view the data. For real GGHL use,
keep the repo PRIVATE and serve it through Cloudflare Pages + Zero Trust
Access (same setup as the salary-increment app) — the identical folder works
there unchanged, and the GitHub Action still refreshes the data.
