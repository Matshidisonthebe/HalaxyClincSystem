HALAXY CLINIC — PUBLIC HOSTING STARTER
======================================

This package is prepared for Render deployment. It uses Python + SQLite and no PHP/WAMP/MySQL.

IMPORTANT: DEMO ONLY
- Do not put real patient information into this demonstration app.
- The example doctor account uses a public demo password; anyone who knows it can access doctor features.
- Before using this publicly beyond a demonstration, change/remove demo credentials, add proper administrator provisioning, security review, rate limiting, audit logs, reliable backups, and appropriate South African privacy safeguards (including POPIA).
- The render.yaml sets HALAXY_DATA_DIR=/var/data. Render persistent disks require a paid web-service plan. If you deploy on a free plan without a disk, the SQLite database may be lost on restarts/redeploys.

PUBLISHING STEPS
1. Create a GitHub account at https://github.com/ if you do not already have one.
2. In GitHub, create a new repository named halaxy-clinic-demo. For the simplest route, choose Private.
3. Open the repository, choose Add file > Upload files. Extract this ZIP first, then upload the files inside the halaxy-sqlite-website folder (app.py, index.html, requirements.txt, render.yaml, and README files). Do NOT upload any clinic_data folder or real data.
4. Click Commit changes.
5. Create a Render account at https://render.com/ and choose New > Blueprint.
6. Connect your GitHub account, select the halaxy-clinic-demo repository, and follow the prompts to apply render.yaml. If asked, approve creation of the web service.
7. Wait for the deployment to finish. Render will show a URL ending in onrender.com. Click it to open your public website.
8. Test with dummy data only.

If you use Render's New > Web Service rather than Blueprint, select the repository and set:
- Runtime: Python 3
- Build Command: pip install -r requirements.txt
- Start Command: python app.py
- Environment variable: HALAXY_DATA_DIR=/var/data (only set this if a persistent disk is attached and mounted at /var/data)

DATABASE NOTE
The included render.yaml expects a disk mounted at /var/data for persistent SQLite data. Add a persistent disk in Render's service settings with mount path /var/data (paid plan). If you do not attach a disk, remove HALAXY_DATA_DIR from the Render environment so the app writes into its temporary service folder; data may disappear on restart/redeploy.

LOCAL USE
The original START-HALAXY.bat still works on Windows.
