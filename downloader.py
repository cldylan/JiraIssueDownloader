import os
import requests
from fpdf import FPDF
import shutil
from config import JIRA_URL, PROJECT_KEY, USERNAME, API_TOKEN

AUTH = (USERNAME, API_TOKEN)
HEADERS = {"Accept": "application/json"}

OUTPUT_DIR = "jira_export"

def fetch_issues(start_at=0, max_results=50):
    url = f"{JIRA_URL}/rest/api/3/search"
    query = {
        'jql': f'project={PROJECT_KEY}',
        'startAt': start_at,
        'maxResults': max_results,
        'fields': 'summary,description,comment,attachment'
    }
    response = requests.get(url, headers=HEADERS, auth=AUTH, params=query)
    return response.json()

def create_pdf(issue_key, issue_data, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(0, 10, f"Issue: {issue_key}", ln=True)
    pdf.cell(0, 10, f"Summary: {issue_data['fields']['summary']}", ln=True)
    
    description = issue_data['fields'].get('description') or "No description"
    pdf.multi_cell(0, 10, f"Description:\n{description}")
    
    comments = issue_data['fields']['comment']['comments']
    pdf.cell(0, 10, "Comments:", ln=True)
    for c in comments:
        pdf.multi_cell(0, 10, f"- {c['author']['displayName']}: {c['body']}")
    
    pdf.output(output_path)

def download_attachments(attachments, folder_path):
    for att in attachments:
        url = att['content']
        filename = att['filename']
        response = requests.get(url, auth=AUTH, stream=True)
        with open(os.path.join(folder_path, filename), 'wb') as f:
            shutil.copyfileobj(response.raw, f)

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    start_at = 0
    max_results = 50
    total = 1  # dummy to enter the loop
    
    while start_at < total:
        data = fetch_issues(start_at, max_results)
        total = data['total']
        
        for issue in data['issues']:
            issue_key = issue['key']
            attachments = issue['fields'].get('attachment', [])
            
            if attachments:
                folder_path = os.path.join(OUTPUT_DIR, issue_key)
                os.makedirs(folder_path, exist_ok=True)
                pdf_path = os.path.join(folder_path, f"{issue_key}.pdf")
                create_pdf(issue_key, issue, pdf_path)
                download_attachments(attachments, folder_path)
            else:
                pdf_path = os.path.join(OUTPUT_DIR, f"{issue_key}.pdf")
                create_pdf(issue_key, issue, pdf_path)
        
        start_at += max_results

    # Create a zip archive of the entire export folder
    shutil.make_archive(OUTPUT_DIR, 'zip', OUTPUT_DIR)

if __name__ == "__main__":
    main()
