# Flipkart: The Road to Profitability

An interactive **teaching simulation** for Managing Digital Transformation. Students balance cost reduction against revenue, satisfaction, second-period retention, cash survival and investor mandates. Includes a password-protected faculty dashboard.

> **Not a Flipkart financial model or prediction.** All coefficients, investor rules, and valuation multiples are illustrative. The case-chart values are used as the starting classroom benchmark.

## What is included?
- `app.py`: Streamlit student and faculty interfaces
- `simulator.py`: transparent economics, elasticities, investor criteria
- `storage.py`: local CSV or persistent Google Sheets storage
- `tests/test_simulator.py`: model correctness tests
- `.streamlit/config.toml`: theme
- `.streamlit/secrets.toml.example`: safe example secrets; *do not commit actual secrets*

## Local setup on Windows / VS Code

Open terminal in the extracted project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
```

Edit `.streamlit/secrets.toml`, replacing the faculty password placeholder. Then:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open `http://localhost:8501`. Test student and faculty tabs. Submission data is saved in `data/submissions.csv` **only locally**.

Run automated tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Deploy using GitHub + Streamlit Community Cloud

1. Create a **new** repository such as `flipkart-profitability-simulator` on GitHub. Upload project contents (not the enclosing folder) including `.streamlit/config.toml`; check hidden-folder uploads are included. Do not upload `.streamlit/secrets.toml`.
2. Visit https://share.streamlit.io, connect GitHub, choose **Create app**, repository, branch `main`, and entrypoint `app.py`.
3. Choose a unique app URL and deploy. Paste your secrets under **Advanced settings → Secrets**, or later under the app's settings.
4. Share the resulting `https://your-app-name.streamlit.app/` link with students. They do not need Python or GitHub; they open it in a browser.
5. **Before the actual class, enable Google Sheets storage** (steps below). Local CSV on Streamlit Community Cloud is temporary, may vanish on restart and is unsafe for concurrent multi-user writes.

## Google Sheets persistence (recommended for class)

1. Create a Google Sheet in your Google account; copy the long ID in its URL between `/d/` and `/edit`.
2. In Google Cloud Console, enable Google Sheets API, create a service account, and create a JSON key if organisation policy allows.
3. Share the Google Sheet with the service account's `client_email` as **Editor**. Never share the key with students.
4. In Streamlit Community Cloud **Secrets** paste TOML like:

```toml
faculty_password = "A_LONG_UNIQUE_SECRET"
spreadsheet_id = "YOUR_SPREADSHEET_ID"

[gcp_service_account]
type = "service_account"
project_id = "PROJECT_ID"
private_key_id = "PRIVATE_KEY_ID"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_KEY\n-----END PRIVATE KEY-----\n"
client_email = "YOUR_SERVICE_ACCOUNT_EMAIL"
client_id = "CLIENT_ID"
token_uri = "https://oauth2.googleapis.com/token"
```

Use values from the service-account JSON. Never commit the JSON/key or local secrets to GitHub. If you previously uploaded them, rotate the key and remove it from repository history.

5. Deploy/restart, submit one test response, then verify it appears in the `Submissions` worksheet and faculty dashboard. Student submissions append to an audit trail; **latest** submission per section/group appears on the dashboard.

## Faculty dashboard

Open the same link as students, select **Faculty dashboard**, and enter the password from Secrets. See a group comparison table, revenue–profit scatter plot, average cost reductions, and a CSV download. Use **Refresh submissions** during debrief. Protect the password; this is simple course-level access, not enterprise authentication.

## Economics and scoring

The image shows revenue of 100 and costs totalling 135:

| Head | Starting cost |
|--|--:|
| Vendors | 65 |
| Discounts | 30 |
| Marketing & promotions | 12 |
| Technology | 8 |
| Logistics | 7 |
| Warehousing | 5 |
| Packaging | 3 |
| Payment gateways | 2 |
| Others | 3 |

Students select **reductions of 0–50% of each head's baseline cost**, rather than allocating percentages of revenue. The simulation computes period-1 orders and period-2 revenue from stylised nonlinear demand penalties; customer satisfaction and retention respond to service reductions. Cost heads have variable versus committed shares. Five investor milestones: period-1 revenue ≥90, period-1 operating loss ≤20, satisfaction ≥70, period-2 revenue ≥90, and end-of-period-2 cash ≥0 (opening cash 35). You can edit assumptions and thresholds in `simulator.py`.

**Important modelling caveats:** This is a simplified *retailer-like* P&L, not full marketplace GMV/take-rate accounting. Discounts are shown as an explicit expense *once* to mirror the case's graphic. It is not a statement about Flipkart's official accounting. Demand and valuation figures are hypothetical teaching assumptions. The valuation proxy is period-2 revenue times a stylised variable multiple; it is NOT a stock-market valuation. A strategy may fail all milestones; that is a valid class outcome.

## Suggested use (30 minutes)

- 5 min: distribute the exhibit and discuss why minimising losses is insufficient.
- 8 min: groups adjust cost reductions and observe P1 effects.
- 5 min: students assess investor funding and P2 retention/cash.
- 5 min: groups refine decisions and submit.
- 7 min: compare results on faculty dashboard; discuss the revenue–profit frontier and long-term value capture.

**Privacy:** Collect a section and group ID only. Students should not enter personal identifying information. If using Google Sheets, control spreadsheet sharing accordingly.

**Data reset:** For local testing, delete `data/submissions.csv` while app is stopped. For Google Sheets, archive or delete rows below the header in `Submissions` after exporting prior-class results.

## Documentation
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
