# Before deploying (step 7)

Checklist for publishing the Streamlit app on Streamlit Community Cloud. Steps 1–6 (shared code, app pages, tests, configuration) are done on the `streamlit-app` branch.

- [ ] **Fork the repository.** Fork `naserhusovic-droid/dsb_capston` on GitHub to your own account. Keep the fork **public**: Community Cloud deploys public repositories without extra access setup.
- [ ] **Connect this checkout to the fork.** This folder's `origin` points to Naser's repository. Add the fork as a second remote and push the `streamlit-app` branch to it, or merge it into the fork's `main` first:
  ```bash
  git remote add fork git@github.com:<your-username>/dsb_capston.git
  git push fork streamlit-app
  ```
- [ ] **Sign in to Streamlit Community Cloud.** Go to [share.streamlit.io](https://share.streamlit.io) and sign in with the GitHub account that owns the fork. This step happens in the browser.
- [ ] **Confirm the data terms.** The app and the public repository republish `data/raw/DTM Europe_Q1_2026_Dataset.xlsx`. Check that the IOM DTM terms of use allow this, and keep the source credit shown in the app footer. If republishing is not allowed, decide on another way to supply the data before deploying.
- [x] **Remove the duplicate workbook.** `DTM Europe_Q1_2026_Dataset (1).xlsx` was identical to the main workbook (same SHA-1) and has been deleted.

## Deploy settings to use (step 7)

| Setting | Value |
| --- | --- |
| Repository | `<your-username>/dsb_capston` |
| Branch | `streamlit-app` (or `main` if merged) |
| Main file path | `app.py` |
| Python version (Advanced settings) | 3.13 |
| Secrets | None needed |

## After deploying

- [ ] The public URL loads in a private or incognito window.
- [ ] All four pages work: Overview, Explore data, Forecasts, Route map.
- [ ] The Forecasts page shows Montenegro: Linear Regression, April 2026 = 478; WBR: Random Forest, April 2026 = 3,591.
- [ ] The map renders and the downloaded forecast CSV matches the table on screen.
- [ ] The deployment logs show no errors.
- [ ] Add the public URL and the deployed commit to `README.md`.
