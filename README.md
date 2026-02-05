# Pratibimb: Agentic Forensic Honey-Pot

Pratibimb is a high-performance, automated forensic honeypot designed to detect, engage, and extract intelligence from social engineering and financial scam attempts. By simulating a believable persona, the system maintains long-term engagement with attackers to maximize intelligence gathering.

## Core Features

- **Dynamic Persona Engagement**: Implements a "retired senior citizen" persona to encourage scammers to reveal tactics and credentials.
- **Forensic Extraction Engine**: Real-time pattern matching for:
  - Financial Identifiers (UPI IDs, Bank Account numbers)
  - Phishing Infrastructure (URLs, IP addresses)
  - Communication Channels (Phone numbers, Emails)
  - Tactical Keywords (Urgency patterns, Social engineering hooks)
- **High-Fidelity Interaction**: Optimized response latency and multi-turn conversational state management.
- **Automated Reporting**: Mandatory callback integration for real-time intelligence feeds.
- **Production Grade Security**: Header-based authentication and secure endpoint structure.

## Technical Architecture

- **Engine**: FastAPI (Python 3.10+)
- **Analysis**: Distributed Forensic Scanner logic
- **Deployment**: Containerized via Docker for cloud-scale execution
- **Intelligence Flow**: Secure POST-based messaging with background-task asynchronous reporting

## Setup & Deployment

### Local Execution
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the service:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8080
   ```

### Production (Docker)
1. Build the image:
   ```bash
   docker build -t pratibimb-api .
   ```
2. Run the container:
   ```bash
   docker run -p 8080:8080 -e APP_API_KEY=your_key pratibimb-api
   ```

## Security Disclosure
This system is intended for authorized security research and defensive intelligence collection. All data extracted is handled according to defined forensic standards.
