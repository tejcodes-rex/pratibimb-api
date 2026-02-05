import re
from typing import Dict, List, Any

class ForensicScanner:
    def __init__(self):
        # Compiled Regex Patterns for efficiency
        self.patterns = {
            "upi_id": re.compile(r'[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}'),
            # Allow - and space in phone numbers, ensure 10-12 digits
            "phone_number": re.compile(r'(?:\+91[\-\s]?)?[6-9]\d{9,11}|(?:\+91[\-\s]?)?[6-9]\d{4}[\-\s]\d{5,6}'),
            "email": re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
            "url": re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'),
            # STRICTER but BROADER Bank Account: 9-18 digits, must be distinct
            "bank_account": re.compile(r'\b\d{9,18}\b'), 
            "suspicious_keywords": re.compile(r'(?i)(otp|kyc|block|prize|lottery|winner|refund|expires|urgent|password|pin|cvv|anydesk|teamviewer|quicksupport|paytm|gpay|phonepe|verify)')
        }
    
    def scan(self, text: str) -> Dict[str, List[str]]:
        """
        Scans the text for patterns and returns a dictionary of findings.
        """
        intelligence = {}
        
        # Run regex scans
        intelligence['upiIds'] = self.patterns['upi_id'].findall(text)
        intelligence['phoneNumbers'] = self.patterns['phone_number'].findall(text)
        intelligence['emails'] = self.patterns['email'].findall(text)
        intelligence['phishingLinks'] = self.patterns['url'].findall(text)
        intelligence['bankAccounts'] = self.patterns['bank_account'].findall(text)
        
        # Keyword detection - return list of found keywords
        intelligence['suspiciousKeywords'] = self.patterns['suspicious_keywords'].findall(text)
        
        # Deduplicate results using set
        for key in intelligence:
            intelligence[key] = list(set(intelligence[key]))
            
        return intelligence

    def analyze_conversation_risk(self, conversation_history: List[Dict]) -> str:
        """
        concatenates recent messages to analyze overall risk or produce 'agentNotes'.
        """
        # Simple implementation: summarize risk based on keywords count
        total_keywords = 0
        for msg in conversation_history:
             if isinstance(msg, dict) and msg.get('sender') == 'scammer':
                 matches = self.patterns['suspicious_keywords'].findall(msg.get('text', ''))
                 total_keywords += len(matches)
        
        if total_keywords > 5:
            return "High Risk: Multiple scam keywords detected."
        elif total_keywords > 0:
            return "Medium Risk: Some suspicious terms used."
        return "Low Risk: Normal conversation flow so far."

    def detect_scam_intent(self, text: str) -> Dict[str, Any]:
        """
        STRICT REQUIREMENT 5: Scam Intent Detection Module.
        Returns { "scamDetected": bool, "confidenceScore": float, "reasons": [] }
        """
        reasons = []
        score = 0.0
        
        # 1. Check Keywords (Urgency, Financial)
        keywords = self.patterns['suspicious_keywords'].findall(text)
        if keywords:
            score += 0.4
            reasons.append(f"Suspicious keywords detected: {', '.join(keywords[:3])}")
            
        # 2. Check Financial Indicators (UPI, Bank)
        if self.patterns['upi_id'].search(text):
            score += 0.3
            reasons.append("UPI ID request detected")
        if self.patterns['bank_account'].search(text):
            score += 0.3
            reasons.append("Bank Details detected")
            
        # 3. Check Links
        if self.patterns['url'].search(text):
            score += 0.2
            reasons.append("Suspicious Link detected")
            
        # 4. Contextual Heuristics (Urgency)
        urgency_terms = ['immediately', 'urgent', 'suspend', 'block', 'expire', '24 hours']
        if any(term in text.lower() for term in urgency_terms):
            score += 0.3
            reasons.append("High Urgency / Threat language detected")

        # Cap score at 1.0
        score = min(score, 1.0)
        
        # Threshold: 0.3 (Low threshold to ensure Honey-Pot triggers for testing)
        is_scam = score >= 0.3
        
        return {
            "scamDetected": is_scam,
            "confidenceScore": round(score, 2),
            "reasons": reasons
        }
