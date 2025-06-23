import os
from typing import Optional
import certifi

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
except ImportError as e:  # pragma: no cover
    # Provide a clear hint if sendgrid is not installed
    raise ImportError("SendGrid package is required. Install with 'pip install sendgrid==6.11.0'") from e


def send_email(to_email: str, subject: str, body: str, *, html_body: Optional[str] = None) -> None:
    """Send an email via SendGrid.

    Parameters
    ----------
    to_email: str
        Recipient's email address.
    subject: str
        Subject line of the email.
    body: str
        Plain‐text email body.
    html_body: Optional[str]
        Optional HTML content for the email; if omitted, the plain‐text body is reused.

    Raises
    ------
    RuntimeError
        If the SENDGRID_API_KEY environment variable is not set.
    Exception
        If the SendGrid API client raises an exception while sending the email (printed to stdout as fallback).
    """
    # Ensure a valid CA bundle is used for TLS verification (works for urllib3 / requests)
    ca_bundle_path = certifi.where()
    os.environ.setdefault("SSL_CERT_FILE", ca_bundle_path)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", ca_bundle_path)

    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        raise RuntimeError("SENDGRID_API_KEY environment variable not set. Email not sent.")

    from_email = os.getenv("FROM_EMAIL", "no-reply@example.com")

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        plain_text_content=body,
        html_content=html_body or body,
    )

    # try:
    #     sg = SendGridAPIClient(api_key)
    #     response = sg.send(message)
    #     # Optionally inspect response.status_code 
    # except Exception as exc:
    #     raise RuntimeError(f"SendGrid send failed: {exc}")

    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        print(f"[SendGrid] Status: {response.status_code}")
    except Exception as exc:
        # Surface SSL errors clearly so you can fix the CA bundle instead of disabling verification.
        raise RuntimeError(
            "SendGrid send failed. Likely cause: TLS certificate validation error. "
            "If you are behind a proxy/antivirus that intercepts HTTPS, export the root certificate "
            "and append it to certifi's cacert.pem, then set SSL_CERT_FILE & REQUESTS_CA_BUNDLE."
        ) from exc


