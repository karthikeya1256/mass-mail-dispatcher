from flask import Flask, render_template, request, Response
import pandas as pd
from io import StringIO

app = Flask(__name__)

# Global storage for downloadable lists
valid_emails_global = []
invalid_emails_global = []

# Email validation function
def is_valid_email(email):
    if not email or '@' not in email or email.count('@') != 1:
        return False

    local, domain = email.split('@')

    if not local or not domain:
        return False
    if ' ' in email or '..' in email:
        return False
    if domain.startswith('.') or domain.endswith('.'):
        return False
    if '.' not in domain:
        return False
    tld = domain.split('.')[-1]
    if len(tld) < 2:
        return False

    return True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_csv():
    try:
        file = request.files['file']
        if not file or not file.filename.endswith('.csv'):
            return "Invalid file. Please upload a CSV.", 400

        content = StringIO(file.stream.read().decode("utf-8"))
        df = pd.read_csv(content)

        possible_columns = [col for col in df.columns if 'email' in col.lower()]
        if possible_columns:
            email_col = possible_columns[0]
            emails = df[email_col].dropna().unique()
        else:
            return "CSV must contain an email-related column.", 400

        valid_emails = []
        invalid_emails = []

        for email in emails:
            if is_valid_email(email):
                valid_emails.append(email)
            else:
                invalid_emails.append(email)

        global valid_emails_global, invalid_emails_global
        valid_emails_global = valid_emails
        invalid_emails_global = invalid_emails

        return render_template('result.html', valid_emails=valid_emails, invalid_emails=invalid_emails)

    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/download-valid')
def download_valid():
    if not valid_emails_global:
        return "No valid emails to download", 400
    data = '\n'.join(valid_emails_global)
    return Response(data, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=valid_emails.csv"})

@app.route('/download-invalid')
def download_invalid():
    if not invalid_emails_global:
        return "No invalid emails to download", 400
    data = '\n'.join(invalid_emails_global)
    return Response(data, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=invalid_emails.csv"})

if __name__ == '__main__':
    app.run(debug=True)
