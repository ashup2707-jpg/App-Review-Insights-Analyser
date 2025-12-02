"""
Layer 4: Email drafter
Creates email draft with weekly pulse note
"""
from datetime import datetime
from typing import Optional
import sys
import os
import smtplib
from email.message import EmailMessage

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger
import config

logger = setup_logger(__name__)


class EmailDrafter:
    """Drafts email with weekly pulse note"""
    
    def __init__(self, recipient: str = None):
        """
        Initialize email drafter.

        Priority for recipient:
        1) Explicit `recipient` argument
        2) EMAIL_RECIPIENT from config (if set)
        3) EMAIL_ADDRESS (sender) as a fallback
        4) Hard-coded team address as last resort
        """
        self.recipient = (
            recipient
            or config.EMAIL_RECIPIENT
            or config.EMAIL_ADDRESS
            or "team@indmoney.com"
        )
        
    def draft_email(self, pulse_content: str) -> str:
        """
        Draft email with pulse content
        
        Args:
            pulse_content: Weekly pulse note content
            
        Returns:
            Email draft as string
        """
        logger.info("Drafting email...")
        
        week_date = datetime.now().strftime("%B %d, %Y")
        
        email = f"""To: {self.recipient}
Subject: IND Money Weekly Product Pulse - Week of {week_date}

Hi Team,

Here is this week’s INDmoney product pulse, based on recent Google Play Store reviews. It is written for a product and leadership audience and focuses on where users are satisfied, where they are facing friction, and what we should do next.

At a glance:
- **Key themes**: What users talk about most, by volume.
- **Exact quotes**: A few short verbatim reviews to keep us close to user reality.
- **Summary & action items**: Concrete follow-ups for the product and engineering roadmap.

Below is the automatically generated pulse for this week:

{pulse_content}

---

How to use this report:
- **Product / Growth**: Turn the action items into specific tickets with owners and timelines; review impact over the next 2–3 sprints.
- **Support**: Use the themes and quotes to update macros/FAQs and proactively address recurring issues.
- **Leadership (CEO/CXO)**: Treat this as a quick health check on UX, reliability, and trust; pay special attention to any themes where negative sentiment is increasing.

This report is auto-generated from publicly available Google Play Store reviews. No personally identifiable information (PII) is included.

Best regards,
IND Money Review Analyzer
"""
        
        return email
    
    def save_draft(self, email_content: str, output_path: str):
        """Save email draft to file"""
        with open(output_path, 'w') as f:
            f.write(email_content)
        logger.info(f"Saved email draft to {output_path}")

    def send_email_from_draft(self, email_content: str) -> bool:
        """
        Optionally send the drafted email to the recipient using SMTP.
        
        This reads EMAIL_ADDRESS / EMAIL_PASSWORD / SMTP_SERVER / SMTP_PORT
        from config. To enable sending, set an environment variable:
        ENABLE_EMAIL_SENDING=1
        """
        enable = os.getenv("ENABLE_EMAIL_SENDING", "").lower() in ("1", "true", "yes")
        if not enable:
            logger.info("Email sending disabled (ENABLE_EMAIL_SENDING not set). Skipping send.")
            return False

        if not (config.EMAIL_ADDRESS and config.EMAIL_PASSWORD):
            logger.warning("Email sending skipped: EMAIL_ADDRESS or EMAIL_PASSWORD is not configured.")
            return False

        # Extract subject and body from the plain-text draft
        lines = email_content.splitlines()
        subject_line = next((l for l in lines if l.startswith("Subject:")), None)
        subject = subject_line.split("Subject:", 1)[1].strip() if subject_line else \
            f"IND Money Weekly Review Pulse - Week of {datetime.now().strftime('%B %d, %Y')}"

        # Body: everything after the first blank line following the Subject
        try:
            subject_index = lines.index(subject_line) if subject_line in lines else 0
        except ValueError:
            subject_index = 0

        body_lines = []
        blank_seen = False
        for line in lines[subject_index + 1:]:
            if not blank_seen:
                if line.strip() == "":
                    blank_seen = True
                continue
            body_lines.append(line)

        body = "\n".join(body_lines) if body_lines else email_content

        msg = EmailMessage()
        msg["From"] = config.EMAIL_ADDRESS
        msg["To"] = self.recipient
        msg["Subject"] = subject
        msg.set_content(body)

        try:
            with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
                server.starttls()
                server.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
                server.send_message(msg)
            logger.info(f"Sent weekly pulse email to {self.recipient}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


def draft_email_from_pulse(pulse_md: str, output_txt: str, recipient: str = None):
    """Draft email from pulse note"""
    
    # Load pulse content
    with open(pulse_md, 'r') as f:
        pulse_content = f.read()
    
    # Draft email
    drafter = EmailDrafter(recipient)
    email = drafter.draft_email(pulse_content)
    drafter.save_draft(email, output_txt)
    
    print("\n" + "="*60)
    print("EMAIL DRAFT")
    print("="*60)
    print(email)
    print("="*60)
    
    return email


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python email_drafter.py <pulse_md> <output_txt> [recipient]")
        sys.exit(1)
    
    pulse_file = sys.argv[1]
    output_file = sys.argv[2]
    recipient = sys.argv[3] if len(sys.argv) > 3 else None
    
    draft_email_from_pulse(pulse_file, output_file, recipient)
