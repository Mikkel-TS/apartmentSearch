import os
import base64
import pickle
from pathlib import Path
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class GmailSender:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.send']
        self.credentials_path = os.path.join(os.path.dirname(__file__), '..', 'credentials')
        os.makedirs(self.credentials_path, exist_ok=True)
        self.token_path = os.path.join(self.credentials_path, 'token.pickle')
        self.credentials_file = os.path.join(self.credentials_path, 'credentials.json')

    def get_gmail_service(self):
        """Gets Gmail API service using stored credentials or new OAuth flow."""
        creds = None
        
        # Load existing token if it exists
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If credentials don't exist or are invalid, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Missing credentials.json file. Please download it from Google Cloud Console "
                        f"and place it in {self.credentials_file}"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for future use
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        return build('gmail', 'v1', credentials=creds)

    def send_email(self, to_email, subject, html_content):
        """Sends an email using Gmail API."""
        try:
            service = self.get_gmail_service()
            
            message = EmailMessage()
            message["To"] = to_email
            message["From"] = os.getenv('EMAIL_ADDRESS')
            message["Subject"] = subject
            message.add_alternative(html_content, subtype='html')

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            sent_message = service.users().messages().send(
                userId="me",
                body={"raw": encoded_message}
            ).execute()
            
            print(f"Email sent successfully to {to_email}")
            return sent_message
            
        except Exception as e:
            print(f"Error sending email via Gmail API: {str(e)}")
            raise 