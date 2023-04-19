import argparse
import logging
import os
import smtplib
import sys
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Optional

import jinja2
import yaml
from dotenv import load_dotenv

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger("send_email")


def generate_email_body(template_path: str, *args: Any, **kwargs: Any) -> str:
    body = ""
    file_path = Path(template_path)
    with file_path.open("r", encoding="UTF-8") as template_file:
        # Render the template with the data
        template_str = template_file.read()
        template_compiled = jinja2.Template(template_str)
        body = template_compiled.render(*args, **kwargs)

    return body


def generate_email(
    from_email: str,
    to_email: str,
    subject_line: str,
    body: str,
    attachment_path: Optional[str] = None,
) -> MIMEMultipart:
    # Create the email message
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject_line
    msg.attach(MIMEText(body, "plain"))

    # Add an attachment (optional)
    if attachment_path is not None:
        file_path = Path(attachment_path)
        file_name = file_path.name
        with file_path.open("rb") as file_to_attach:
            attachment = MIMEApplication(file_to_attach.read(), _subtype="pdf")
            attachment.add_header(
                "Content-Disposition", "attachment", filename=file_name
            )
            msg.attach(attachment)

    return msg


def send_email(
    msg: MIMEMultipart,
    smtp_server: str,
    smtp_port: int,
    gmail_login: str,
    gmail_password: str,
) -> None:
    # Send the email
    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(gmail_login, gmail_password)
        smtp.sendmail(msg["From"], msg["To"], msg.as_string())


# Arguments:
# Path to template
# Path to data
# Recipient first name
# Recipient last name
# Recipient email address
# Path to file containing gmail parameters - optional (can read from environment or .env file)

load_dotenv()

# Define command line arguments
parser = argparse.ArgumentParser(description="Send an email based on a template.")
parser.add_argument("-template", help="Path to the email template (Jinja2).")
parser.add_argument("-data", help="Path to YAML file containing template data.")
parser.add_argument("-recipient_email", help="Recipient email address.")
parser.add_argument("-recipient_first_name", help="The first name of the recipient.")
parser.add_argument("-recipient_last_name", help="The last name of the recipient.")
parser.add_argument("-subject", help="Subject line of email.")

# Parse the command line arguments
args = parser.parse_args()
template = args.template
data = args.data
recipient_email = args.recipient_email
recipient_first = args.recipient_first_name
recipient_last = args.recipient_last_name
subject = args.subject

logger.debug("Template path = %s", template)
logger.debug("Template data path = %s", data)
logger.debug("Recipient email = %s", recipient_email)
logger.debug("Recipient first = %s", recipient_first)
logger.debug("Recipient last = %s", recipient_last)
logger.debug("Subject = %s", subject)

# Load YAML template data into dictionary
template_data = {}
data_path = Path(data)
with data_path.open("r", encoding="UTF-8") as data_file:
    data_doc = data_file.read()
    template_data = yaml.safe_load(data_doc)
logger.debug("Template data: %s", template_data)

from_email = os.getenv("GMAIL_LOGIN_EMAIL")
gmail_smtp_server = os.getenv("GMAIL_SMTP_SERVER")
gmail_smtp_port = os.getenv("GMAIL_SMTP_PORT")
gmail_password = os.getenv("GMAIL_LOGIN_PASSWORD")

logger.debug("Gmail SMTP server = %s", gmail_smtp_server)
logger.debug("Gmail SMTP port first = %s", gmail_smtp_port)
logger.debug("Gmail Login email = %s", from_email)

provided_vars = {
    "recipient_first_name": recipient_first,
    "recipient_last_name": recipient_last,
    "recipient_email": recipient_email,
    "subject": subject,
}
email_body = generate_email_body(template, {**provided_vars, **template_data})
logger.debug("Email body = %s", email_body)

email_message = generate_email(
    from_email, args.recipient_email, args.subject, email_body
)
send_email(
    email_message, gmail_smtp_server, gmail_smtp_port, from_email, gmail_password
)
