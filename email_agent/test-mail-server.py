"""
test_mail_api.py

A lightweight REST API for TESTING purposes only.
Mimics how your real company mail API will behave (POST endpoint that sends an email),
but uses Gmail SMTP under the hood — so you can test your AI agent's REST call flow
before you get access to the actual company mail API.

Install dependencies:
    pip install flask

Run:
    python test_mail_api.py
    (Server starts at http://localhost:5000)

Test it:
    curl -X POST http://localhost:5000/send-email \
      -H "Content-Type: application/json" \
      -d '{
            "recipient_emails": ["you@example.com"],
            "subject": "Test Email",
            "body": "This is a test.",
            "is_html": false
          }'

Gmail setup:
    - Use a Gmail account with 2-Step Verification enabled
    - Generate an App Password: https://myaccount.google.com/apppasswords
    - Set SENDER_EMAIL and SENDER_APP_PASSWORD below (or as environment variables)
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Configure these (or set as environment variables) ---
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "adilshaikh5991@gmail.com")
SENDER_APP_PASSWORD = os.environ.get("SENDER_APP_PASSWORD", "dqagbnrqnmtvvddy")


def send_email(recipient_emails, subject, body, is_html=False, cc_emails=None, bcc_emails=None):
    """Sends an email via Gmail SMTP. Returns a dict with success status."""
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = ", ".join(recipient_emails)
        msg["Subject"] = subject

        if cc_emails:
            msg["Cc"] = ", ".join(cc_emails)

        content_type = "html" if is_html else "plain"
        msg.attach(MIMEText(body, content_type))

        all_recipients = list(recipient_emails)
        if cc_emails:
            all_recipients += cc_emails
        if bcc_emails:
            all_recipients += bcc_emails

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, all_recipients, msg.as_string())

        return {"success": True, "message": f"Email sent to {len(all_recipients)} recipient(s)."}

    except Exception as e:
        return {"success": False, "message": f"Failed to send email: {str(e)}"}


@app.route("/send-email", methods=["POST"])
def send_email_endpoint():
    """
    REST endpoint that mimics the shape of a production mail API.
    Expects JSON body:
    {
        "recipient_emails": ["a@example.com"],
        "subject": "Subject line",
        "body": "Email body text or HTML",
        "is_html": false,
        "cc_emails": [],       # optional
        "bcc_emails": []       # optional
    }
    """
    data = request.get_json(force=True, silent=True)

    if not data:
        return jsonify({"success": False, "message": "Invalid or missing JSON body."}), 400

    recipient_emails = data.get("recipient_emails")
    subject = data.get("subject")
    body = data.get("body")
    is_html = data.get("is_html", False)
    cc_emails = data.get("cc_emails")
    bcc_emails = data.get("bcc_emails")

    if not recipient_emails or not subject or not body:
        return jsonify({
            "success": False,
            "message": "Missing required fields: recipient_emails, subject, body"
        }), 400

    result = send_email(recipient_emails, subject, body, is_html, cc_emails, bcc_emails)
    status_code = 200 if result["success"] else 500
    return jsonify(result), status_code


@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
