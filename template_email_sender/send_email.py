"""Command line utility to send a templated email

Raises:
    FileNotFoundError: if template or data file not found
    SystemExit: to exit the program upon error

Returns:
"""
import argparse
import logging
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from . import template_email

logging.basicConfig(
    filename="template-email-sender.log",
    filemode="w",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("send_email")

COMMAND_NAME = "send_email"


def print_cli_error(msg: str) -> None:
    """_summary_

    Args:
        msg (str): _description_
    """
    print(f"{COMMAND_NAME}: {msg}")


if __name__ == "__main__":
    # Arguments:
    # Path to template
    # Path to data
    # Recipient first name
    # Recipient last name
    # Recipient email address
    # Path to file containing gmail parameters - optional
    # (can read from environment or .env file)

    load_dotenv()

    # Define command line arguments
    parser = argparse.ArgumentParser(description="Send an email based on a template.")
    parser.add_argument(
        "-template", help="Path to the email template (Jinja2).", required=False
    )
    parser.add_argument(
        "-data", help="Path to YAML file containing template data.", required=True
    )
    parser.add_argument(
        "-recipient_email", help="Recipient email address.", required=True
    )
    parser.add_argument(
        "-recipient_first_name", help="The first name of the recipient.", required=True
    )
    parser.add_argument(
        "-recipient_last_name", help="The last name of the recipient.", required=True
    )
    parser.add_argument("-subject", help="Subject line of email.", required=True)

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

    provided_vars = {
        "recipient_first_name": recipient_first,
        "recipient_last_name": recipient_last,
        "recipient_email": recipient_email,
        "subject": subject,
    }

    from_email = os.getenv("GMAIL_LOGIN_EMAIL")
    gmail_smtp_server = os.getenv("GMAIL_SMTP_SERVER")
    gmail_smtp_port = os.getenv("GMAIL_SMTP_PORT")
    gmail_password = os.getenv("GMAIL_LOGIN_PASSWORD")

    logger.debug("Gmail SMTP server = %s", gmail_smtp_server)
    logger.debug("Gmail SMTP port first = %s", gmail_smtp_port)
    logger.debug("Gmail Login email = %s", from_email)

    try:
        # Load YAML template data into dictionary
        template_data = {}
        data_path = Path(data)

        with data_path.open("r", encoding="UTF-8") as data_file:
            data_doc = data_file.read()
            template_data = yaml.safe_load(data_doc)
        logger.debug("Template data: %s", template_data)
        if not template:
            template = template_data["template_file"]

        template_path = Path(template)
        email_body = template_email.generate_email_body(
            template_path, {**provided_vars, **template_data, "from_email": from_email}
        )
        logger.debug("Email body = %s", email_body)

        email_message = template_email.generate_email(
            from_email, args.recipient_email, args.subject, email_body
        )
        template_email.send_email(
            email_message,
            gmail_smtp_server,
            gmail_smtp_port,
            from_email,
            gmail_password,
        )
    except Exception as e:
        logger.exception(e)
        print_cli_error(str(e))
        raise SystemExit(1) from e
