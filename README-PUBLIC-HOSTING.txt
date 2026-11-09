HALAXY CLINIC — PUBLIC HOSTING STARTER
======================================

IMPORTANT: DEMO ONLY
- Do not put real patient information into this demonstration app.
- The example doctor account uses a public demo password; anyone who knows it can access doctor features.
- Before using this publicly beyond a demonstration, change/remove demo credentials, add proper administrator provisioning, security review, rate limiting, audit logs, reliable backups, and appropriate South African privacy safeguards (including POPIA).
- The render.yaml sets HALAXY_DATA_DIR=/var/data. Render persistent disks require a paid web-service plan. If you deploy on a free plan without a disk, the SQLite database may be lost on restarts/redeploys.


DATABASE NOTE
The included render.yaml expects a disk mounted at /var/data for persistent SQLite data. Add a persistent disk in Render's service settings with mount path /var/data (paid plan). If you do not attach a disk, remove HALAXY_DATA_DIR from the Render environment so the app writes into its temporary service folder; data may disappear on restart/redeploy.

LOCAL USE
The original START-HALAXY.bat still works on Windows.
