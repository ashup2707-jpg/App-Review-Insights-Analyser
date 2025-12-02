"""
Layer 4: Email drafter
Creates email draft with weekly pulse note
"""
from datetime import datetime
from typing import Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger
import config

logger = setup_logger(__name__)


class EmailDrafter:
    """Drafts email with weekly pulse note"""
    
    def __init__(self, recipient: str = None):
        """Initialize email drafter"""
        self.recipient = recipient or config.EMAIL_ADDRESS or "team@indmoney.com"
        
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
Subject: IND Money Weekly Review Pulse - Week of {week_date}

Hi Team,

Here's your weekly pulse on IND Money app reviews. This summary highlights the top themes, user feedback, and recommended actions based on the last 8-12 weeks of reviews.

{pulse_content}

---

**How to Use This Report:**
- **Product/Growth**: Focus on top themes and action items for feature prioritization
- **Support**: Review user quotes to understand pain points and improve responses
- **Leadership**: Quick pulse on user sentiment and key areas needing attention

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
