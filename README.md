# Apartment Search Script

A Python script that searches for apartments using OpenAI's GPT-4 model and sends results via email.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   EMAIL_ADDRESS=your_email@gmail.com
   EMAIL_PASSWORD=your_app_specific_password
   RECIPIENT_EMAIL=recipient@email.com
   ```

   Note: For Gmail, you'll need to use an App-Specific Password. Generate one at: https://myaccount.google.com/apppasswords

3. Customize search parameters in `apartment_search.py` if needed:
   - Location
   - Maximum price
   - Minimum number of rooms

## Usage

Run the script:
```
python apartment_search.py
```

The script will:
1. Search for apartments using OpenAI
2. Log results to `apartment_search.log`
3. Send results via email to the specified recipient
