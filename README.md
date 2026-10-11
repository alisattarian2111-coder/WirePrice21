# WirePrice PWA

A Persian RTL installable web app for browsing publicly listed wire/cable prices from multiple Iranian sources. It is designed for GitHub Pages and phone-only setup.

## Files
- `index.html`, `manifest.json`, `sw.js`, `icon.svg`: PWA front end.
- `prices.json`: refreshed data read by the app.
- `update_prices.py`: best-effort parser for public price-list pages.
- `.github/workflows/update-prices.yml`: scheduled daily run (05:25 UTC) and manual run.

## Setup on GitHub Pages
1. Upload these files to repository root: `index.html`, `manifest.json`, `sw.js`, `icon.svg`, `prices.json`, `update_prices.py`.
2. Create a new file with this exact path: `.github/workflows/update-prices.yml`, then paste the workflow YAML from the provided package into it. Keep the other files in the repository root.
3. In Settings → Actions → General, ensure workflow permissions allow read/write repository contents if the workflow cannot push.
4. Settings → Pages → Deploy from a branch → `main` → `/(root)`.
5. Actions → Update cable prices → Run workflow for the first refresh. Scheduled runs occur daily.
6. Open the Pages site and install from Chrome.

The collector is best-effort and depends on each website's public HTML structure and availability. It does not bypass logins or anti-bot controls. If a source changes structure, the collector may return no records for that source. Prices can be per meter, per ring, excluding VAT, or list prices; verify source, unit, date and final quote before using commercially. No prices are fabricated.
