from utils.search import (
    search_andelsbolig,
    search_rental,
    process_search_results,
    send_email_report
)
import os
import logging

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