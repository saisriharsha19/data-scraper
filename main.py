import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import make_msgid
from bs4 import BeautifulSoup
import requests
import sys
import os
import time
import uuid
from dotenv import load_dotenv


load_dotenv()
SMTP_PORT = os.getenv('SMTP_PORT')
SMTP_SERVER = os.getenv('SMTP_SERVER')
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')
log_file = "job_log.txt"
sys.stdout = open(log_file, 'w')  



def scrape_new_job_listings():
    url = "https://explore.jobs.ufl.edu/en-us/filter/?search-keyword=&work-type=student%20ast&work-type=temp%20part-time&job-mail-subscribe-privacy=agree"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Failed to fetch the website: {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    job_table = soup.find("tbody", id="search-results-content")
    if not job_table:
        print("Could not find the job listings table.")
        return []
    print(job_table)
    rows = job_table.find_all("tr")
    jobs = []
    table_body = soup.find("tbody", id="search-results-content")
    if not table_body:
        return None

    rows = table_body.find_all("tr")
    for i in range(0, len(rows), 2):
        main_row = rows[i]
        title = main_row.find("a", class_="job-link").text.strip()
        link = "https://explore.jobs.ufl.edu/" + main_row.find("a", class_="job-link")["href"]
        department = main_row.find("span", class_="job-department").text.strip()
        location = main_row.find("span", class_="location").text.strip()
        close_time = main_row.find("time")
        closing_date = close_time["datetime"] if close_time else None
        

        summary_row = rows[i + 1]
        summary = summary_row.text.strip()
        
        jobs.append({
            "title": title,
            "link": link,
            "department": department,
            "location": location,
            "closing_date": closing_date,
            "summary": summary,
        })

    return jobs[:20]

def send_email(job_listings):
    try:
        subject = "UF Careers Job Listings (Last Hour)"
        html_body = """
        <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    background-color: #f4f4f9;
                    color: #333;
                    padding: 20px;
                }
                h2 {
                    color: #2C3E50;
                }
                ul {
                    list-style-type: none;
                    padding-left: 0;
                }
                li {
                    background-color: #ffffff;
                    border: 1px solid #ddd;
                    padding: 10px;
                    margin-bottom: 10px;
                    border-radius: 8px;
                }
                li strong {
                    color: #2C3E50;
                }
                .job-details {
                    margin-top: 10px;
                }
                .job-details li {
                    font-size: 14px;
                    margin-bottom: 5px;
                }
                .link {
                    color: #2980B9;
                    text-decoration: none;
                }
                .link:hover {
                    text-decoration: underline;
                }
                .job-list {
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: #fff;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
            </style>
        </head>
        <body>
            <div class="job-list">
                <h2>Latest Job Listings:</h2>
                <ul>
        """
        number = 1
        for job in job_listings:
            html_body += f"""
                <li>
                    <strong>{number}. {job['title']}</strong><br>
                    <ul class="job-details">
                        <li><strong>Link To Apply:</strong> <a class="link" href="{job['link']}">{job['link']}</a></li>
                        <li><strong>Department:</strong> {job['department']}</li>
                        <li><strong>Location:</strong> {job['location']}</li>
                        <li><strong>Closing Date:</strong> {job['closing_date']}</li>
                        <li><strong>Summary:</strong> {job['summary']}</li>
                    </ul>
                </li>
            """
            number += 1
        html_body += """
                </ul>
            </div>
        </body>
        </html>
        """

        list_of_emails = RECIPIENT_EMAIL.split(",")
        for email in list_of_emails:
            msg_id = f"<{uuid.uuid4()}--{email}--{time.time()}"
            print(msg_id)
            message = MIMEMultipart()
            message["From"] = EMAIL_ADDRESS
            message["To"] = email
            message["Subject"] = subject
            message["Message-ID"] = msg_id
            message.attach(MIMEText(html_body, "html"))
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, email, message.as_string())
            server.quit()
            print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    job_listings = scrape_new_job_listings()
    if job_listings:
        send_email(job_listings)
    else:
        print("No job listings found.")
    sys.stdout.close()
    del sys.stdout
    os.remove(log_file)