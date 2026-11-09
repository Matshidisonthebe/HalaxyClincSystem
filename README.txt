HALAXY CLINIC — FREE PUBLIC HOSTING SETUP (DEMO)
================================================
This edition is adapted for a static host (Netlify) and Supabase cloud authentication/database. It does not use PHP, WAMP, or a Python server at runtime.

IMPORTANT
- This is a demonstration project, NOT ready for real patient/medical records.
- Do not put real patient information in this demo. Production healthcare use requires professional security, privacy, access-control, backup, and legal review.
- Supabase Free projects can pause after a week of inactivity and have quotas. Netlify Free also has usage limits. Check their current terms.
- The Supabase anon/publishable key is intended for browser use ONLY when Row Level Security (RLS) policies are enabled. NEVER paste a Supabase service_role/secret key into index.html.

PART A — CREATE SUPABASE BACKEND
1. Go to https://supabase.com/ and create a free account/project.
2. Open the project dashboard > SQL Editor > New query.
3. Open supabase-schema.sql from this ZIP, copy all its contents into the SQL editor, and click Run.
4. In Supabase project settings, find the Project URL and anon/public key (sometimes labelled publishable key).
5. Open index.html in a text editor (Notepad is fine).
6. Near the top of the JavaScript, replace:
   PASTE_SUPABASE_PROJECT_URL_HERE
   PASTE_SUPABASE_ANON_KEY_HERE
   with your own Project URL and anon/public key. Keep the quotes around the values.
7. In Supabase Authentication settings, configure the allowed Site URL and redirect URL after your Netlify URL is created. Keep email confirmation enabled where possible; users may need to confirm their email before logging in.

PART B — CREATE A PUBLIC URL ON NETLIFY
1. Extract this ZIP.
2. Go to https://app.netlify.com/drop (sign up/log in if prompted).
3. Drag the extracted halaxy-free-cloud folder onto the drop area. Upload the folder itself containing index.html and netlify.toml, not the ZIP file.
4. Netlify should publish it and give you a public URL ending in netlify.app.
5. Add that URL to Supabase Authentication > URL Configuration as the Site URL and an allowed redirect URL.
6. Refresh your Netlify URL and test registration/login using demo accounts only.

PART C — CREATE A DOCTOR ACCOUNT (ADMIN ACTION)
Public signup deliberately creates patient accounts only. To promote your own account to doctor:
1. Register an account from your public site and confirm your email if requested.
2. In Supabase Dashboard > SQL Editor, run this query after replacing the email:
   update public.profiles set role='doctor' where email='YOUR-EMAIL@example.com';
3. Log out and log back in. Only promote an account you control.

FEATURES
- Patient registration/login (Supabase Auth)
- Patient dashboard and appointment requests
- Doctor dashboard, appointment approval/completion/cancellation
- Patient list and payment history display
- Clinic settings and JSON export
- Cloud Postgres database with row-level security policies

LIMITATIONS / SETUP NOTES
- This is a conversion from the previous Python/SQLite demo to Supabase. It needs the URL/key and SQL setup above before it can work.
- Email confirmations may mean a newly registered user must confirm their email before logging in.
- A doctor account must be promoted manually in Supabase as described above.
- Payments are records only; this does not process real payments.
- Do not publish the Supabase service_role key or any secret key in the browser.
