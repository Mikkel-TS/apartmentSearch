import os
import logging
from datetime import datetime
import json
import yagmail
import openai
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    filename='apartment_search.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')

def search_apartments(search_parameters):
    """
    Search for apartments using OpenAI to process web results
    """
    prompt = f"""
    Please search for available apartments with the following criteria:
    - Location: {search_parameters['location']}
    - Max Price: {search_parameters['max_price']}
    - Min Rooms: {search_parameters['min_rooms']}
    
    Please search across:
    1. Facebook Marketplace
    2. Local real estate websites
    3. Popular rental platforms
    
    Format the results as a structured list with:
    - Property address
    - Price
    - Number of rooms
    - Link to listing (if available)
    - Source (website/platform)
    - Key features
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that searches for apartment listings."},
                {"role": "user", "content": prompt}
            ]
        )
        print(response)
        
        return response.choices[0].message['content']
    except Exception as e:
        logging.error(f"Error in OpenAI API call: {str(e)}")
        return None

def send_email_report(results, recipient_email):
    """
    Send search results via email
    """
    try:
        # Initialize yagmail SMTP object
        yag = yagmail.SMTP(os.getenv('EMAIL_ADDRESS'), os.getenv('EMAIL_PASSWORD'))
        
        # Format email subject
        subject = f"Apartment Search Results - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Send email
        yag.send(
            to=recipient_email,
            subject=subject,
            contents=results
        )
        
        logging.info(f"Email sent successfully to {recipient_email}")
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}")

def main():
    # Search parameters
    search_parameters = {
        'location': 'Copenhagen',
        'max_price': 15000,
        'min_rooms': 2
    }
    
    # Recipient email
    recipient_email = os.getenv('RECIPIENT_EMAIL')
    
    # Log search start
    logging.info(f"Starting apartment search with parameters: {json.dumps(search_parameters)}")
    print(f"Starting apartment search with parameters: {json.dumps(search_parameters)}")
    
    # Perform search
    results = search_apartments(search_parameters)
    
    if results:
        # Log results
        logging.info("Search completed successfully")
        logging.info(f"Results:\n{results}")
        print(f"Results:\n{results}")
        # Send email
        send_email_report(results, recipient_email)
    else:
        logging.error("No results found or error occurred during search")

if __name__ == "__main__":
    main() 