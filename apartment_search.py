import os
import logging
from datetime import datetime
import json
import yagmail
import openai
from tavily import TavilyClient
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
tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

# Define target areas
TARGET_AREAS = ["Vesterbro", "Østerbro", "Frederiksberg", "Indre by", "Nørrebro", "Valby", "Christianshavn"]
AREAS_STRING = ", ".join(TARGET_AREAS)

def search_andelsbolig():
    """
    Search for Andelsbolig listings
    """
    try:
        ANDELS_QUERY = (
            '("andelsbolig" OR "andelslejlighed") '
            '(Vesterbro OR Østerbro OR Frederiksberg OR "København K" OR Nørrebro OR Valby OR Christianshavn) '
            '("til salg" OR sælges) '
            '("60..100 m2" OR "60..100 kvm") '
            '-solgt -reserveret '
            '(site:dba.dk OR site:bolighub.dk OR site:boligzonen.dk OR '
            'site:boligportal.dk OR site:findboliger.dk OR site:facebook.com/marketplace)'
        )
        
        print(f"Søger efter andelsboliger med søgning: {ANDELS_QUERY}")
        
        search_result = tavily.search(
            query=ANDELS_QUERY,
            search_depth="advanced",
            max_results=15
        )
        
        return search_result
    except Exception as e:
        print(f"Fejl i andelsbolig-søgning: {str(e)}")
        logging.error(f"Fejl i andelsbolig-søgning: {str(e)}")
        return None

def search_rental():
    """
    Search for rental apartments
    """
    try:
        # ---------- 2) Lejeboliger – klassiske sites ----------
        RENT_QUERY_1 = (
            '("lejlighed" OR lejebolig) '
            '(Vesterbro OR Østerbro OR Frederiksberg OR "København K" OR Nørrebro OR Valby OR Christianshavn) '
            '("til leje" OR udlejes) '
            '("60..100 m2" OR "60..100 kvm") '
            '-kollegium -værelse -fremleje -møbleret -udlejet '
            '(site:boligportal.dk OR site:lejebolig.dk OR site:findbolig.nu)'
        )

        # ---------- 3) Lejeboliger – DBA + Facebook ----------
        RENT_QUERY_2 = (
            '("lejlighed" OR lejebolig) '
            '(Vesterbro OR Østerbro OR Frederiksberg OR "København K" OR Nørrebro OR Valby OR Christianshavn) '
            '("til leje" OR udlejes) '
            '("60..100 m2" OR "60..100 kvm") '
            '("kr/md" OR "pr måned") '
            '-kollegium -værelse -fremleje -møbleret -udlejet '
            '(site:dba.dk OR site:facebook.com/marketplace)'
        )

        print(f"Søger efter lejeboliger (del 1) med søgning: {RENT_QUERY_1}")
        
        results1 = tavily.search(
            query=RENT_QUERY_1,
            search_depth="advanced",
            max_results=10
        )
        
        print(f"Søger efter lejeboliger (del 2) med søgning: {RENT_QUERY_2}")
        
        results2 = tavily.search(
            query=RENT_QUERY_2,
            search_depth="advanced",
            max_results=10
        )
        
        # Combine results
        combined_results = {
            'query': 'Combined rental search',
            'results': results1.get('results', []) + results2.get('results', [])
        }
        
        return combined_results
    except Exception as e:
        print(f"Fejl i lejebolig-søgning: {str(e)}")
        logging.error(f"Fejl i lejebolig-søgning: {str(e)}")
        return None

def process_search_results(andelsbolig_results, rental_results):
    """
    Use OpenAI to process and structure both search results
    """
    try:
        prompt = f"""
            Du er bolig-dataassistent. Svar KUN med gyldig JSON.

            ############################
            ##  INPUT                  #
            ############################
            {{"andelsbolig_raw": {json.dumps(andelsbolig_results)},
            "rental_raw":      {json.dumps(rental_results)}}}

            ############################
            ##  KRITERIER              #
            ############################
            Fælles:
            - Min. 60 m²
            - Område skal ligge i én af: {AREAS_STRING}

            Andelsboliger:
            - Max pris 3 000 000 DKK

            Lejeboliger:
            - Max leje 25 000 DKK / md

            ############################
            ##  OUTPUT-FORMAT          #
            ############################
            Returnér **KUN** ét JSON-objekt med EXAKT denne struktur:

            {{
            "summary": "<kort dansk tekst max 4 linjer, fx '5 andelsboliger og 7 lejeboliger matcher. Billigste andel: …'>",

            "andelsboliger": [
                {{
                "address":        "<string>",
                "price_dkk":      <integer>,          // totalpris
                "sqm":            <integer>,
                "url":            "<string>",
                "source":         "<domain>",
                "area":           "<Vesterbro|Østerbro|…>",
                "key_features":   "<kort sætning>",
                "missing_fields": ["price_dkk", "sqm"] // tom array hvis ingen mangler
                }}  // max 10, sorter stigende på price_dkk
            ],

            "lejeboliger": [
                {{
                "address":        "<string>",
                "rent_dkk":       <integer>,          // månedlig leje
                "sqm":            <integer>,
                "url":            "<string>",
                "source":         "<domain>",
                "area":           "<Vesterbro|Østerbro|…>",
                "key_features":   "<kort sætning>",
                "missing_fields": ["rent_dkk", "sqm"] // tom array hvis ingen mangler
                }}  // max 10, sorter stigende på rent_dkk
            ]
            }}

            ############################
            ##  REGLER                 #
            ############################
            1. Medtag kun annoncer der matcher ALLE kriterier.
            2. Hvis et felt ikke kan udtrækkes, sæt feltet til null og tilføj navnet i "missing_fields".
            3. Fjern dubletter (samme url eller adresse+sqm).
            4. Ingen kommentarer eller forklaringer uden for JSON!
            """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Du er en hjælpsom assistent der behandler boligannoncer. Formatér informationen klart og verificér at annoncerne matcher søgekriterierne. Kommuniker på dansk."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message['content']
    except Exception as e:
        print(f"Fejl i OpenAI behandling: {str(e)}")
        logging.error(f"Fejl i OpenAI behandling: {str(e)}")
        return None

def send_email_report(results, recipient_email):
    """
    Send search results via email
    """
    try:
        print(f"Attempting to send email to: {recipient_email}")
        print(f"Using email address: {os.getenv('EMAIL_ADDRESS')}")
        
        if not os.getenv('EMAIL_ADDRESS') or not os.getenv('EMAIL_PASSWORD'):
            raise ValueError("Email credentials not found in .env file")
            
        if not recipient_email:
            raise ValueError("Recipient email not found in .env file")

        # Initialize yagmail SMTP object
        print("Initializing SMTP connection...")
        yag = yagmail.SMTP({
            os.getenv('EMAIL_ADDRESS'): "Apartment Search"
        }, os.getenv('EMAIL_PASSWORD'))
        
        # Format email subject and body
        subject = f"Apartment Search Results - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Create a properly formatted HTML body
        html_content = f"""
        <html>
        <body>
        <h2>Apartment Search Results</h2>
        <p>Hva så, Sophie ?!</p>
        <pre style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
{results}
        </pre>
        <p>Med Venlig Hilsen,<br>
        Mikkels Lejligheds Søger</p>
        </body>
        </html>
        """
        
        print("Sending email...")
        # Send email with both HTML and plain text
        yag.send(
            to=recipient_email,
            subject=subject,
            contents=[
                html_content,
                results
            ]
        )
        
        print(f"Email sent successfully to {recipient_email}")
        logging.info(f"Email sent successfully to {recipient_email}")
    except ValueError as ve:
        error_msg = f"Configuration error: {str(ve)}"
        print(error_msg)
        logging.error(error_msg)
        raise
    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        print(error_msg)
        logging.error(error_msg)
        raise

def main():
    # Recipient email
    recipient_email = os.getenv('RECIPIENT_EMAIL')
    
    # Log search start
    print("Starter boligsøgning...")
    
    # Perform Andelsbolig search
    print("\nSøger efter andelsboliger...")
    andelsbolig_results = search_andelsbolig()
    
    # Perform rental search
    print("\nSøger efter lejeboliger...")
    rental_results = search_rental()
    
    if andelsbolig_results or rental_results:
        print("\nBehandler søgeresultater...")
        # Process results with OpenAI
        processed_results = process_search_results(andelsbolig_results, rental_results)
        
        if processed_results:
            # Log results
            logging.info("Søgning gennemført med succes")
            logging.info(f"Resultater:\n{processed_results}")
            print(f"Resultater:\n{processed_results}")
            
            # Send email
            try:
                send_email_report(processed_results, recipient_email)
                print("Email sendt med succes")
            except Exception as e:
                print(f"Fejl ved afsendelse af email: {str(e)}")
        else:
            print("Kunne ikke behandle søgeresultater")
            logging.error("Kunne ikke behandle søgeresultater")
    else:
        print("Ingen søgeresultater fundet eller der opstod en fejl under søgningen")
        logging.error("Ingen søgeresultater fundet eller der opstod en fejl under søgningen")

if __name__ == "__main__":
    main() 