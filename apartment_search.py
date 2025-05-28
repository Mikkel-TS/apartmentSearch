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
        # Split into multiple smaller searches for each site
        all_results = []
        
        # DBA Search
        dba_query = '("andelsbolig" OR "andelslejlighed") København "til salg" -solgt site:dba.dk/andelsbolig'
        print("Søger DBA...")
        dba_results = tavily.search(query=dba_query, search_depth="advanced", max_results=5)
        if dba_results and 'results' in dba_results:
            all_results.extend(dba_results['results'])

        # Facebook Search
        fb_query = 'andelslejlighed København "til salg" -solgt -bytte site:facebook.com/marketplace'
        print("Søger Facebook...")
        fb_results = tavily.search(query=fb_query, search_depth="advanced", max_results=5)
        if fb_results and 'results' in fb_results:
            all_results.extend(fb_results['results'])

        print(f"Found {len(all_results)} results")
        print(json.dumps(all_results, indent=4))
        return {'results': all_results}
    except Exception as e:
        print(f"Fejl i andelsbolig-søgning: {str(e)}")
        logging.error(f"Fejl i andelsbolig-søgning: {str(e)}")
        return None

def search_rental():
    """
    Search for rental apartments
    """
    try:
        all_results = []

        # Boligportal Search
        boligportal_query = 'lejlighed København "til leje" -udlejet site:boligportal.dk/lejeboliger'
        print("Søger Boligportal...")
        bp_results = tavily.search(query=boligportal_query, search_depth="advanced", max_results=5)
        if bp_results and 'results' in bp_results:
            all_results.extend(bp_results['results'])

        # Boligportal Search
        andelsbolig_query = 'andelsbolig København "til salg" -solgt site:andelsboliger.dk'
        print("Søger Andelsboliger.dk...")
        ab_results = tavily.search(query=andelsbolig_query, search_depth="advanced", max_results=5)
        if ab_results and 'results' in ab_results:
            all_results.extend(ab_results['results'])

        # Lejebolig.dk Search
        lejebolig_query = 'lejlighed København "til leje" -udlejet site:lejebolig.dk/lejebolig'
        print("Søger Lejebolig.dk...")
        lb_results = tavily.search(query=lejebolig_query, search_depth="advanced", max_results=5)
        if lb_results and 'results' in lb_results:
            all_results.extend(lb_results['results'])

        # DBA Search
        dba_query = 'lejlighed København "til leje" -udlejet site:dba.dk/lejebolig'
        print("Søger DBA...")
        dba_results = tavily.search(query=dba_query, search_depth="advanced", max_results=5)
        if dba_results and 'results' in dba_results:
            all_results.extend(dba_results['results'])

        # Facebook Search
        fb_query = 'lejlighed København "til leje" -udlejet site:facebook.com/marketplace'
        print("Søger Facebook...")
        fb_results = tavily.search(query=fb_query, search_depth="advanced", max_results=5)
        if fb_results and 'results' in fb_results:
            all_results.extend(fb_results['results'])

        print(f"Found {len(all_results)} results")
        print(json.dumps(all_results, indent=4))
        return {'results': all_results}
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
            - STRIKT minimum 45 m² (ignorer ALT under 45)
            - STRIKT maximum 140 m² (ignorer ALT over 140)
            - Område skal ligge i én af: {AREAS_STRING}
            - URL skal være direkte link til en specifik bolig (ikke søgeresultater eller kategorisider)
            - Ignorer hvis URL indeholder: "/search", "/soeg", "?soeg=", "/item/"
            - Tjek at URL matcher det rigtige website (fx dba.dk links skal starte med "dba.dk/andelsbolig" eller "dba.dk/lejebolig")

            Andelsboliger:
            - Max pris 3 000 000 DKK
            - Ignorer hvis beskrivelse indeholder: "solgt", "reserveret", "overtaget"

            Lejeboliger:
            - Max leje 25 000 DKK / md
            - Ignorer hvis beskrivelse indeholder: "udlejet", "er desværre udlejet"

            ############################
            ##  OUTPUT-FORMAT          #
            ############################
            Returnér **KUN** ét JSON-objekt med EXAKT denne struktur:

            {{
            "summary": "<kort dansk tekst der PRÆCIST matcher antallet af viste boliger i JSON>",

            "andelsboliger": [
                {{
                "address":        "<string>",
                "price_dkk":      <integer>,          // totalpris
                "sqm":            <integer>,
                "url":            "<string>",         // SKAL være direkte link til bolig
                "source":         "<domain>",
                "area":           "<Vesterbro|Østerbro|…>",
                "key_features":   "<kort sætning>",
                "missing_fields": ["price_dkk", "sqm"] // tom array hvis ingen mangler
                }}  // sorter stigende på price_dkk
            ],

            "lejeboliger": [
                {{
                "address":        "<string>",
                "rent_dkk":       <integer>,          // månedlig leje
                "sqm":            <integer>,
                "url":            "<string>",         // SKAL være direkte link til bolig
                "source":         "<domain>",
                "area":           "<Vesterbro|Østerbro|…>",
                "key_features":   "<kort sætning>",
                "missing_fields": ["rent_dkk", "sqm"] // tom array hvis ingen mangler
                }}  // sorter stigende på rent_dkk
            ]
            }}

            ############################
            ##  REGLER                 #
            ############################
            1. Medtag KUN annoncer der matcher ALLE kriterier - vær MEGET striks med dette.
            2. Hvis et felt ikke kan udtrækkes, sæt feltet til null og tilføj navnet i "missing_fields".
            3. Fjern dubletter (samme url eller adresse+sqm).
            4. Summary SKAL matche det faktiske antal viste boliger i JSON output.
            5. Ingen kommentarer eller forklaringer uden for JSON!
            6. VIGTIG URL VALIDERING:
               - Ignorer URLs der indeholder: "/search", "/soeg", "?soeg=", "/item/"
               - Ignorer URLs der ikke er direkte links til specifikke boliger
               - Tjek at domænet matcher kilden (fx dba.dk links skal starte med "dba.dk/andelsbolig" eller "dba.dk/lejebolig")
            7. VIGTIG INDHOLDSVALIDERING:
               - Ignorer annoncer med tekst der indikerer at boligen er utilgængelig ("udlejet", "solgt", etc.)
               - Ignorer annoncer der er søgeresultatsider eller kategorisider
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
        
        # Parse the results as JSON to ensure proper formatting
        results_json = json.loads(results) if isinstance(results, str) else results
        
        # Format the results in a more readable way
        formatted_results = []
        
        # Add summary
        if 'summary' in results_json:
            formatted_results.append(f"<h3>Oversigt</h3>")
            formatted_results.append(f"<p>{results_json['summary']}</p>")
        
        # Format andelsboliger
        if 'andelsboliger' in results_json:
            formatted_results.append("<h3>Andelsboliger</h3>")
            for bolig in results_json['andelsboliger']:
                formatted_results.append("<div style='margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; border-radius: 5px;'>")
                formatted_results.append(f"<strong>Adresse:</strong> {bolig.get('address', 'Ikke angivet')}<br>")
                formatted_results.append(f"<strong>Pris:</strong> {bolig.get('price_dkk', 'Ikke angivet'):,} DKK<br>".replace(',', '.') if bolig.get('price_dkk') else "<strong>Pris:</strong> Ikke angivet<br>")
                formatted_results.append(f"<strong>Størrelse:</strong> {bolig.get('sqm', 'Ikke angivet')} m²<br>")
                formatted_results.append(f"<strong>Område:</strong> {bolig.get('area', 'Ikke angivet')}<br>")
                formatted_results.append(f"<strong>Beskrivelse:</strong> {bolig.get('key_features', 'Ingen beskrivelse')}<br>")
                formatted_results.append(f"<strong>Link:</strong> <a href='{bolig.get('url', '#')}'>{bolig.get('source', 'Link')}</a><br>")
                formatted_results.append("</div>")
        
        # Format lejeboliger
        if 'lejeboliger' in results_json:
            formatted_results.append("<h3>Lejeboliger</h3>")
            for bolig in results_json['lejeboliger']:
                formatted_results.append("<div style='margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; border-radius: 5px;'>")
                formatted_results.append(f"<strong>Adresse:</strong> {bolig.get('address', 'Ikke angivet')}<br>")
                formatted_results.append(f"<strong>Månedlig leje:</strong> {bolig.get('rent_dkk', 'Ikke angivet'):,} DKK<br>".replace(',', '.') if bolig.get('rent_dkk') else "<strong>Månedlig leje:</strong> Ikke angivet<br>")
                formatted_results.append(f"<strong>Størrelse:</strong> {bolig.get('sqm', 'Ikke angivet')} m²<br>")
                formatted_results.append(f"<strong>Område:</strong> {bolig.get('area', 'Ikke angivet')}<br>")
                formatted_results.append(f"<strong>Beskrivelse:</strong> {bolig.get('key_features', 'Ingen beskrivelse')}<br>")
                formatted_results.append(f"<strong>Link:</strong> <a href='{bolig.get('url', '#')}'>{bolig.get('source', 'Link')}</a><br>")
                formatted_results.append("</div>")

        # Format email subject and body
        subject = f"Boligsøgning Resultater - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Create a properly formatted HTML body
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                h2, h3 {{ color: #2c3e50; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                a {{ color: #3498db; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Boligsøgning Resultater</h2>
                {''.join(formatted_results)}
                <p style="margin-top: 30px; color: #7f8c8d;">
                    Med Venlig Hilsen,<br>
                    Boligsøgnings Bot
                </p>
            </div>
        </body>
        </html>
        """
        
        print("Sending email...")
        # Send email with both HTML and plain text
        yag.send(
            to=recipient_email,
            subject=subject,
            contents=[html_content]
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