## Jira Project Issues Downloader

Download issues from a Jira project to local PDFs with their attachments, and package them into a zip. This script uses the Jira Cloud REST API and fpdf2 to render issue summaries, descriptions, and comments into a per-issue PDF.

### What it does
- Authenticates to Jira using an API token
- Queries all issues for a project key
- Generates a PDF per issue with basic metadata, description, and comments
- Downloads issue attachments to subfolders
- Creates a `jira_export.zip` archive of the exported folder

---

## Requirements
- Python 3 (3.8+ recommended)
- A Jira Cloud account with access to the target project
- Jira API token for your account

Python dependencies are listed in `requirements.txt`:
- requests
- fpdf2

## Setup (Windows PowerShell)
1) Install dependencies

```powershell
pip install -r requirements.txt
```

2) Configure credentials and project

```powershell
Copy-Item config-template.py config.py -Force
```

Edit `config.py` and set:
- `JIRA_URL`    e.g., https://yourcompany.atlassian.net
- `PROJECT_KEY` e.g., ABC
- `USERNAME`    your Atlassian email/login
- `API_TOKEN`   your Jira API token (create one in your Atlassian account security settings)

Keep `config.py` private and out of source control.

## Run
From this folder:

```powershell
python downloader.py
```

Expected output:
- A folder `jira_export/` containing PDFs per issue and attachments in subfolders
- A zip archive `jira_export.zip` with the same contents

Fonts: the script uses bundled Noto Sans fonts from `fonts/` for PDF rendering.

## Troubleshooting
- Module not found (requests/fpdf): ensure you ran `pip install -r requirements.txt`.
- 401/403 errors: verify `USERNAME` and `API_TOKEN`, and that your account has access to the project. Ensure `JIRA_URL` is correct for your site.
- 404 errors: check `PROJECT_KEY` and that the project exists.

## Project layout
- `downloader.py` — main script (fetch issues, render PDFs, download attachments, zip output)
- `config-template.py` — sample configuration; copy to `config.py` and fill in your values
- `requirements.txt` — Python dependencies
- `fonts/` — Noto Sans fonts used by fpdf2
- `jira_export/` — export output which will be created upon execution
- `jira_export.zip` — export output archive which will be created at the end of execution

## Security notes
- Treat `config.py` as sensitive. Do not commit your API token.
- Principle of least privilege: ensure the account used has only the access required.
