from utils.search import (
    search_andelsbolig,
    search_rental,
    process_search_results,
    send_email_report
)
import os
import json
import logging

def load_recipients():
    """
    Load recipient emails from mapping.json
    """
    try:
        with open('mapping.json', 'r') as f:
            mapping = json.load(f)
            return mapping.get('recipients', [])
    except Exception as e:
        print(f"Error loading mapping.json: {str(e)}")
        return []

def main():
    # Load recipients from mapping
    recipients = load_recipients()
    if not recipients:
        print("No recipients found in mapping.json")
        return
    
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
            
            # Send email to each recipient
            for recipient in recipients:
                try:
                    email = recipient.get('email')
                    name = recipient.get('name', 'Unknown')
                    if email:
                        print(f"\nSender email til {name} ({email})...")
                        send_email_report(processed_results, email)
                        print(f"Email sendt med succes til {email}")
                    else:
                        print(f"Manglende email for modtager: {name}")
                except Exception as e:
                    print(f"Fejl ved afsendelse af email til {email}: {str(e)}")
        else:
            print("Kunne ikke behandle søgeresultater")
            logging.error("Kunne ikke behandle søgeresultater")
    else:
        print("Ingen søgeresultater fundet eller der opstod en fejl under søgningen")
        logging.error("Ingen søgeresultater fundet eller der opstod en fejl under søgningen")

if __name__ == "__main__":
    main() 