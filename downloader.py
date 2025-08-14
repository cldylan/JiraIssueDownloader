"""
Jira Project Issues Downloader
Author: Dylan Callahan

This script allows the user to download issues from a Jira project, including their comments and attachments. It saves each issue as a PDF file and downloads any associated attachments.

This tool requires a configuration file (config.py) for authentication and project settings.

This script requires the following libraries within the Python environment you are running it in: requests, fpdf
These are also listed in requirements.txt for easier installation
"""
import os
import requests
from fpdf import FPDF
import shutil
from config import JIRA_URL, PROJECT_KEY, USERNAME, API_TOKEN

AUTH = (USERNAME, API_TOKEN)
HEADERS = {"Accept": "application/json"}
OUTPUT_DIR = "jira_export"
CHUNK_SIZE = 8192  # 8KB chunks for downloading attachments, feel free to change


def fetch_issues(start_at=0, max_results=50):
    """
    Fetch issues from the Jira API.
    
    Parameters
    ----------
    start_at : int
        The index of the first issue to return (for pagination).
    max_results : int
        The maximum number of issues to return.
    
    Returns
    ----------
    dict
        The JSON response from the Jira API containing the issues.
    """
    url = f"{JIRA_URL}/rest/api/3/search"
    query = {
        'jql': f'project = "{PROJECT_KEY}"',
        'startAt': start_at,
        'maxResults': max_results,
        'fields': 'issuetype,project,summary,description,comment,attachment'
    }
    response = requests.get(url, headers=HEADERS, auth=AUTH, params=query)
    response.raise_for_status()
    return response.json()


def get_description_text(description):
    if not description:
        return "No description"
    # If it's already a string
    if isinstance(description, str):
        return description
    # If it's a dict (Jira storage format)
    if isinstance(description, dict):
        text = []
        def parse_content(content_list):
            for item in content_list:
                if 'text' in item:
                    text.append(item['text'])
                if 'content' in item:
                    parse_content(item['content'])
        parse_content(description.get('content', []))
        return "\n".join(text) or "No description"
    return str(description)


def create_pdf(issue_key, issue_data, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Add fonts
    pdf.add_font('NotoSans', '', 'fonts/NotoSans-Regular.ttf')
    pdf.add_font('NotoSans', 'B', 'fonts/NotoSans-Bold.ttf')
    pdf.set_font('NotoSans', '', 10)

    # Header
    pdf.set_font('NotoSans', 'B', 12)
    pdf.cell(0, 8, f"{issue_key} - {issue_data['fields']['summary']}")
    pdf.ln(10)

    # Metadata table
    pdf.set_font('NotoSans', '', 10)
    metadata = {
        "Projet": issue_data['fields'].get('project', {}).get('name', ''),
        "Type": issue_data['fields'].get('issuetype', {}).get('name', ''),
        "Priority": issue_data['fields'].get('priority', {}).get('name', ''),
        "Reporter": issue_data['fields'].get('reporter', {}).get('displayName', ''),
        "Assignee": issue_data['fields'].get('assignee', {}).get('displayName', ''),
    }

    for key, value in metadata.items():
        pdf.cell(40, 6, f"{key}:", border=1)
        pdf.cell(0, 6, f"{value}", border=1)
        pdf.ln(6)

    # Description
    description = get_description_text(issue_data['fields'].get('description'))
    pdf.ln(4)
    pdf.set_font('NotoSans', 'B', 10)
    pdf.cell(0, 6, "Description:")
    pdf.ln(6)
    pdf.set_font('NotoSans', '', 10)
    pdf.multi_cell(0, 6, description)

    # Comments
    pdf.ln(4)
    pdf.set_font('NotoSans', 'B', 10)
    pdf.cell(0, 6, "Comments:")
    pdf.ln(6)
    pdf.set_font('NotoSans', '', 10)
    for c in issue_data['fields']['comment']['comments']:
        author = c['author']['displayName']
        created = c['created']
        body = c['body']
        pdf.multi_cell(0, 6, f"{author} ({created}): {body}")
        pdf.ln(2)

    pdf.output(output_path)


def download_attachments(attachments, folder_path):
    """
    Download attachments for a Jira issue.
    
    Parameters
    ----------
    attachments : list
        A list of attachment metadata from the Jira issue.
    folder_path : str
        The path to the folder where attachments will be saved.
    """
    for att in attachments:
        url = att['content']
        filename = att['filename']
        response = requests.get(url, auth=AUTH, stream=True)
        response.raise_for_status()
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(CHUNK_SIZE):
                if chunk:  # filter out keep-alive chunks
                    f.write(chunk)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    start_at = 0
    max_results = 50
    total = 1

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

    shutil.make_archive(OUTPUT_DIR, 'zip', OUTPUT_DIR)


if __name__ == "__main__":
    main()
