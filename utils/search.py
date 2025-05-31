import os
import logging
import json
from datetime import datetime
import yagmail
import openai
from tavily import TavilyClient
from dotenv import load_dotenv
from .filter import filter_tavily_results

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
        all_results = []
        
        # DBA Search
        dba_query = '("andelsbolig" OR "andelslejlighed") København "til salg" -solgt -bytte site:dba.dk/andelsbolig'
        print("Søger DBA...")
        dba_results = tavily.search(query=dba_query, search_depth="advanced", max_results=5)
        if dba_results and 'results' in dba_results:
            filtered_results = filter_tavily_results(dba_results, 'andelsbolig')
            all_results.extend(filtered_results['results'])

        # Facebook Search
        fb_query = 'andelslejlighed København "til salg" -solgt -bytte site:facebook.com/marketplace'
        print("Søger Facebook...")
        fb_results = tavily.search(query=fb_query, search_depth="advanced", max_results=5)
        if fb_results and 'results' in fb_results:
            filtered_results = filter_tavily_results(fb_results, 'andelsbolig')
            all_results.extend(filtered_results['results'])

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

        BoligportalQueries = [
            '3 vær lejlighed københavn Ø inurl:-id- site:boligportal.dk/lejligheder/k%C3%B8benhavn',
            '3 vær lejlighed Vesterbro inurl:-id- site:boligportal.dk/lejligheder/k%C3%B8benhavn',
            '3 vær lejlighed frederiksberg inurl:-id- site:boligportal.dk/lejligheder/k%C3%B8benhavn',
            '3 vær lejlighed nørrebro inurl:-id- site:boligportal.dk/lejligheder/k%C3%B8benhavn',
            '3 vær lejlighed København K inurl:-id- site:boligportal.dk/lejligheder/k%C3%B8benhavn',
            '2 vær lejlighed københavn Ø inurl:-id- site:boligportal.dk/lejligheder/k%C3%B8benhavn',
            '2 vær lejlighed Vesterbro inurl:-id- site:boligportal.dk/lejligheder/k%C3%B8benhavn',
            '2 vær lejlighed frederiksberg inurl:-id- site:boligportal.dk/lejligheder/k%C3%B8benhavn',
            '2 vær lejlighed nørrebro inurl:-id- site:boligportal.dk/lejligheder/k%C3%B8benhavn',
            '2 vær lejlighed København K inurl:-id- site:boligportal.dk/lejligheder/k%C3%B8benhavn',
        ]

        for query in BoligportalQueries:
            print(f"Søger Boligportal med query: {query}")
            bp_results = tavily.search(query=query, search_depth="advanced", max_results=5)
            if bp_results and 'results' in bp_results:
                filtered_results = filter_tavily_results(bp_results, 'lejebolig')
                all_results.extend(filtered_results['results'])

        # Lejebolig.dk Search
        lejebolig_query = 'lejlighed København "til leje" -udlejet site:lejebolig.dk/lejebolig'
        print("Søger Lejebolig.dk...")
        lb_results = tavily.search(query=lejebolig_query, search_depth="advanced", max_results=5)
        if lb_results and 'results' in lb_results:
            filtered_results = filter_tavily_results(lb_results, 'lejebolig')
            all_results.extend(filtered_results['results'])

        # DBA Search
        dba_query = 'lejlighed København "til leje" -udlejet site:dba.dk/lejebolig'
        print("Søger DBA...")
        dba_results = tavily.search(query=dba_query, search_depth="advanced", max_results=5)
        if dba_results and 'results' in dba_results:
            filtered_results = filter_tavily_results(dba_results, 'lejebolig')
            all_results.extend(filtered_results['results'])

        # Facebook Search
        fb_query = 'lejlighed København "til leje" -udlejet site:facebook.com/marketplace'
        print("Søger Facebook...")
        fb_results = tavily.search(query=fb_query, search_depth="advanced", max_results=5)
        if fb_results and 'results' in fb_results:
            filtered_results = filter_tavily_results(fb_results, 'lejebolig')
            all_results.extend(filtered_results['results'])

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
        print("Debug: Input to process_search_results:")
        print(f"andelsbolig_results: {json.dumps(andelsbolig_results, indent=2)}")
        print(f"rental_results: {json.dumps(rental_results, indent=2)}")
        
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
            - Størrelse: Forsøg at udtrække fra titel (fx "93m2" eller "93 m²") eller beskrivelse
            - STRIKT minimum 45 m² (ignorer ALT under 45)
            - STRIKT maximum 140 m² (ignorer ALT over 140)
            - Område skal ligge i én af: {AREAS_STRING}
            - URL skal være direkte link til en specifik bolig (ikke søgesider)

            Andelsboliger:
            - Max pris 3 000 000 DKK hvis prisen er angivet
            - Ignorer hvis beskrivelse indeholder: "solgt", "reserveret", "overtaget"

            Lejeboliger:
            - Max leje 20 000 DKK / md hvis lejen er angivet
            - Ignorer hvis beskrivelse indeholder: "udlejet", "er desværre udlejet"

            ############################
            ##  PARSING REGLER         #
            ############################
            1. Størrelse: 
               - Led efter mønstre som "93m2", "93 m²", "93 kvm" i titel og beskrivelse
               - Hvis størrelse findes i titel (fx "93m2-3-vaer"), brug dette tal
               - Hvis flere størrelser nævnes, brug den første

            2. Område:
               - Tjek for områdenavne i både titel og beskrivelse
               - Brug fuzzy matching (fx "Østerbro" matcher også "Oesterbro" og "København Ø")
               
            3. URL validering:
               - URL må ikke indeholde: "/search", "/soeg", "?soeg=", "/marketplace/search"
               - URL skal indeholde specifikt ID eller adresse
               - Ignorer kategori- og søgesider

            ############################
            ##  OUTPUT FORMAT          #
            ############################
            {{
                "summary": "<kort dansk tekst der matcher antallet af viste boliger>",
                "andelsboliger": [
                    {{
                        "address": "<string>",
                        "price_dkk": <integer eller null>,
                        "sqm": <integer eller null>,
                        "url": "<string>",
                        "source": "<domain>",
                        "area": "<Vesterbro|Østerbro|…>",
                        "key_features": "<kort sætning>",
                        "missing_fields": ["price_dkk", "sqm"]
                    }}
                ],
                "lejeboliger": [
                    {{
                        "address": "<string>",
                        "rent_dkk": <integer eller null>,
                        "sqm": <integer eller null>,
                        "url": "<string>",
                        "source": "<domain>",
                        "area": "<Vesterbro|Østerbro|…>",
                        "key_features": "<kort sætning>",
                        "missing_fields": ["rent_dkk", "sqm"]
                    }}
                ]
            }}

            ############################
            ##  REGLER                 #
            ############################
            1. Inkluder bolig hvis:
               - URL er et direkte link til en specifik bolig
               - Område matcher en af de tilladte områder
               - Hvis størrelse er kendt: mellem 45-140 m²
               - Hvis pris er kendt: under maksimum
            2. Hvis et felt ikke kan udtrækkes, sæt det til null og tilføj i missing_fields
            3. Fjern dubletter (samme url eller adresse+sqm)
            4. Summary skal matche det faktiske antal viste boliger
            """
        
        response = openai.ChatCompletion.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "Du er en hjælpsom assistent der behandler boligannoncer. Formatér informationen klart og verificér at annoncerne matcher søgekriterierne. Kommuniker på dansk."},
                {"role": "user", "content": prompt}
            ]
        )
        
        result = response.choices[0].message['content']
        print("Debug: OpenAI response:")
        print(result)
        
        # Clean the response - remove markdown code block if present
        if result.startswith('```'):
            result = result.split('```')[1]  # Get content between first and second ```
            if result.startswith('json'):
                result = result[4:]  # Remove 'json' prefix
            result = result.strip()
        
        # Validate JSON before returning
        try:
            json.loads(result)  # Test if it's valid JSON
            return result
        except json.JSONDecodeError as je:
            print(f"Debug: Invalid JSON returned from OpenAI: {je}")
            return None
            
    except Exception as e:
        print(f"Fejl i OpenAI behandling: {str(e)}")
        logging.error(f"Fejl i OpenAI behandling: {str(e)}")
        return None

def send_email_report(results, recipient_email):
    """
    Send search results via email
    """
    try:
        print(f"Debug: Results input to send_email_report:")
        print(f"Type: {type(results)}")
        print(f"Value: {results}")
        
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
            formatted_results.append("<h3>Oversigt</h3>")
            formatted_results.append(f"<p>{results_json['summary']}</p>")
        
        # Format andelsboliger
        if 'andelsboliger' in results_json:
            formatted_results.append("<h3>Andelsboliger</h3>")
            for bolig in results_json['andelsboliger']:
                formatted_results.append('<div class="listing">')
                formatted_results.append(f"<p><strong>Adresse:</strong> {bolig.get('address', 'Ikke angivet')}</p>")
                formatted_results.append(f"<p><strong>Pris:</strong> {bolig.get('price_dkk', 'Ikke angivet'):,} DKK</p>".replace(',', '.') if bolig.get('price_dkk') else "<p><strong>Pris:</strong> Ikke angivet</p>")
                formatted_results.append(f"<p><strong>Størrelse:</strong> {bolig.get('sqm', 'Ikke angivet')} m²</p>")
                formatted_results.append(f"<p><strong>Område:</strong> {bolig.get('area', 'Ikke angivet')}</p>")
                formatted_results.append(f"<p><strong>Beskrivelse:</strong> {bolig.get('key_features', 'Ingen beskrivelse')}</p>")
                formatted_results.append(f"<p><strong>Link:</strong> <a href='{bolig.get('url', '#')}'>{bolig.get('source', 'Link')}</a></p>")
                formatted_results.append("</div>")
        
        # Format lejeboliger
        if 'lejeboliger' in results_json:
            formatted_results.append("<h3>Lejeboliger</h3>")
            for bolig in results_json['lejeboliger']:
                formatted_results.append('<div class="listing">')
                formatted_results.append(f"<p><strong>Adresse:</strong> {bolig.get('address', 'Ikke angivet')}</p>")
                formatted_results.append(f"<p><strong>Månedlig leje:</strong> {bolig.get('rent_dkk', 'Ikke angivet'):,} DKK</p>".replace(',', '.') if bolig.get('rent_dkk') else "<p><strong>Månedlig leje:</strong> Ikke angivet</p>")
                formatted_results.append(f"<p><strong>Størrelse:</strong> {bolig.get('sqm', 'Ikke angivet')} m²</p>")
                formatted_results.append(f"<p><strong>Område:</strong> {bolig.get('area', 'Ikke angivet')}</p>")
                formatted_results.append(f"<p><strong>Beskrivelse:</strong> {bolig.get('key_features', 'Ingen beskrivelse')}</p>")
                formatted_results.append(f"<p><strong>Link:</strong> <a href='{bolig.get('url', '#')}'>{bolig.get('source', 'Link')}</a></p>")
                formatted_results.append("</div>")

        # Format email subject
        subject = f"Boligsøgning Resultater - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Create HTML email with proper CSS
        css = """
            body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }
            h2, h3 { color: #2c3e50; margin-top: 20px; }
            .container { max-width: 800px; margin: 0 auto; padding: 20px; }
            .listing { margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background-color: #fff; }
            a { color: #3498db; text-decoration: none; }
            a:hover { text-decoration: underline; }
            p { margin: 8px 0; }
            .footer { margin-top: 30px; color: #7f8c8d; border-top: 1px solid #eee; padding-top: 20px; }
        """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>{css}</style>
        </head>
        <body>
            <div class="container">
                <h2>Boligsøgning Resultater (Under udvikling - Cest la vie)</h2>
                {''.join(formatted_results)}
                <div class="footer">
                    <p>Med Venlig Hilsen,<br>Mikkel</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        print("Sending email...")
        # Send email with HTML content
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