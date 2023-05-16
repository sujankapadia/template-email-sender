import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Optional

import jinja2


environment = jinja2.Environment(autoescape=True)


def generate_email_body(template_path: Path, *args: Any, **kwargs: Any) -> str:
    """Renders an email template given a set of configuration key value pairs.

    Args:
        template_path (Path): path to email Jinja2 template

    Raises:
        FileNotFoundError: if template file not fo und

    Returns:
        str: rendered email template
    """
    body = ""
    try:
        with template_path.open("r", encoding="UTF-8") as template_file:
            # Render the template with the data
            template_str = template_file.read()
            template_compiled = environment.from_string(template_str)
            body = template_compiled.render(*args, **kwargs)
    except FileNotFoundError:
        raise FileNotFoundError(f"No such template file: {template_path}") from None

    return body


def generate_email(
    from_email: str,
    to_email: str,
    subject_line: str,
    body: str,
    attachment_path: Optional[Path] = None,
) -> MIMEMultipart:
    """Generates a MIMEMultipart email message structure

    Args:
        from_email (str): From email address
        to_email (str): To email address
        subject_line (str): Email subject line
        body (str): Email body text
        attachment_path (Optional[str], optional): Attachment. Defaults to None.

    Returns:
        MIMEMultipart: MIMEMultipart email message structure
    """
    # Create the email message
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject_line
    msg.attach(MIMEText(body, "plain"))

    # Add an attachment (optional)
    if attachment_path is not None:
        file_name = attachment_path.name
        with attachment_path.open("rb") as file_to_attach:
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
    """Sends the given MIMEMultipart email message using the provided the SMTP parameters.

    Args:
        msg (MIMEMultipart): email
        smtp_server (str): SMTP server
        smtp_port (int): SMTP port
        gmail_login (str): GMail login email address
        gmail_password (str): GMail password
    """
    # Send the email
    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(gmail_login, gmail_password)
        smtp.sendmail(msg["From"], msg["To"], msg.as_string())
