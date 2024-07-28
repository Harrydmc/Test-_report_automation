import requests
import pandas as pd
from paramiko import SSHClient, AutoAddPolicy
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Function to download QRadar reports
def download_qradar_report(api_url, report_name, api_token, output_file):
    headers = {'SEC': api_token, 'Content-Type': 'application/json'}
    response = requests.get(f"{api_url}/api/ariel/searches/{report_name}/results", headers=headers)
    if response.status_code == 200:
        with open(output_file, 'w') as file:
            file.write(response.text)
        print(f"{report_name} downloaded successfully.")
    else:
        print(f"Failed to download {report_name}: {response.status_code}, {response.text}")

# Function to perform SSH commands and download files via SCP
def download_files_via_ssh(host, port, username, password, remote_path, local_path):
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(host, port=port, username=username, password=password)
    
    sftp = ssh.open_sftp()
    sftp.get(remote_path, local_path)
    sftp.close()
    ssh.close()

# Function to update the Average EPS Tracker
def update_avg_eps_tracker(eps_report_files, tracker_file):
    tracker = pd.read_excel(tracker_file, sheet_name=None)
    for report_file in eps_report_files:
        df = pd.read_csv(report_file)
        avg_fps_60s = df['Avg_FPS_60s'].mean()
        tracker['Sheet1'].loc['Avg_FPS_60s'] = avg_fps_60s
    tracker.to_excel(tracker_file, index=False)
    print("Average EPS Tracker updated.")

# Function to send email with attachments
def send_email(smtp_server, port, sender_email, receiver_email, subject, body, attachments):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    for attachment in attachments:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(attachment, 'rb').read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {attachment}")
        msg.attach(part)

    server = smtplib.SMTP(smtp_server, port)
    server.starttls()
    server.login(sender_email, 'your_password')
    server.sendmail(sender_email, receiver_email, msg.as_string())
    server.quit()

# Example usage
api_url = 'https://your-qradar-instance/api'
api_token = 'your_api_token'
eps_report_files = ['report1.csv', 'report2.csv']
tracker_file = 'Tracker - Avg EPS during business hours.xlsx'

# Download reports
download_qradar_report(api_url, 'Log_Only_Report', api_token, 'log_only_report.csv')
download_qradar_report(api_url, 'Drop_Only_Report', api_token, 'drop_only_report.csv')

# Update trackers
update_avg_eps_tracker(eps_report_files, tracker_file)

# Send email
send_email('smtp.your-email.com', 587, 'your_email@example.com', 'receiver@example.com', 
           'Daily Health Checks for GSOC', 'Attached are the daily health check reports.', 
           ['log_only_report.csv', 'drop_only_report.csv', tracker_file])
