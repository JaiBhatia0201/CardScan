import os
from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
import io
import re
import json 
import requests 
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
from pdf2image import convert_from_path, convert_from_bytes
import pandas as pd
from typing import List, Dict

# --- ENVIRONMENT FIX (REMOVED INSECURE TRANSPORT SETTING) ---
# NOTE: The 'OAUTHLIB_INSECURE_TRANSPORT' line is correctly REMOVED for HTTPS deployment.

# --- GOOGLE API IMPORTS ---
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleAuthRequest
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# --- ENVIRONMENT SETUP: LOAD ALL SECRETS FROM .ENV ---
from dotenv import load_dotenv 
load_dotenv()

# --- API KEY CONFIGURATIONS (Loaded from environment) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
SCOPES = ['https://www.googleapis.com/auth/contacts']




# Initialize the Flask application
app = Flask(__name__)
# CRITICAL: Use a production-safe secret key (e.g., from environment variable)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', '2c9a13b5f0e7d4c2a1b9e8f7c6d5e4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7')

# --- Configuration (Unchanged) ---
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
TESSERACT_CONFIG = r'-l eng --oem 3 --psm 6'

# --- API HELPERS (Unchanged) ---
def generate_structured_data_via_ai(raw_text: str) -> Dict[str, str]:
    if not GEMINI_API_KEY:
        print("-> SKIPPING Gemini API call: Key is missing.")
        return {
            'Name': '', 'Designation': '', 'Company': '', 'Phone': '', 
            'Email': '', 'Address': '', 'Website': '', 
            'Raw_Text_Placeholder': re.sub(r'\s+', ' ', raw_text).strip()
        }

    print("-> Querying Gemini API for structured data...")
    
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "Name": {"type": "STRING", "description": "The person's full name."},
            "Designation": {"type": "STRING", "description": "The job title or role."},
            "Company": {"type": "STRING", "description": "The company name."},
            "Phone": {"type": "STRING", "description": "The primary phone number, standardized to include country code."},
            "Email": {"type": "STRING", "description": "The primary email address."},
            "Website": {"type": "STRING", "description": "The company's website URL."},
            "Address": {"type": "STRING", "description": "The full office address (combine multiple lines)."}
        }
    }

    user_prompt = f"""You are an expert business card transcription service. 
    Analyze the following raw OCR text from a business card and extract the requested fields. 
    If a field is missing, return an empty string ('').
    RAW TEXT: 
    ---
    {raw_text}
    ---
    """
    
    payload = {
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": { 
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
    }
    
    try:
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}", 
            headers=headers, 
            data=json.dumps(payload),
            timeout=30 
        )
        response.raise_for_status() 
        
        result = response.json()
        
        if not result.get('candidates'):
            error_message = result.get('error', {}).get('message', 'Unknown API Error')
            print(f"ERROR: Gemini API returned an error: {error_message}")
            raise KeyError("API did not return structured candidates.")

        json_string = result['candidates'][0]['content']['parts'][0]['text']
        structured_data = json.loads(json_string)
        
        structured_data['Raw_Text_Placeholder'] = re.sub(r'\s+', ' ', raw_text).strip()
        
        print("-> Successfully extracted data via Gemini API.")
        return structured_data

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to connect to Gemini API. Check API Key and network: {e}")
    except KeyError:
        print("ERROR: Gemini response structure was unexpected or API returned a non-candidate error.")
    except json.JSONDecodeError:
        print("ERROR: Gemini did not return valid JSON.")
    
    print("-> Falling back to empty contact data.")
    return {
        'Name': '', 'Designation': '', 'Company': '', 'Phone': '', 
        'Email': '', 'Address': '', 'Website': '', 
        'Raw_Text_Placeholder': re.sub(r'\s+', ' ', raw_text).strip()
    }

# --- IMAGE AND FILE UTILITIES (Unchanged) ---
def preprocess_image(img: Image.Image) -> Image.Image:
    img = img.convert('L')
    threshold = 128
    img = img.point(lambda x: 0 if x < threshold else 255, '1')
    return img

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_ocr(filepath: str) -> List[str]:
    # --- NOTE: PDF processing will likely fail on Render's default environment. ---
    extracted_texts = []
    filename = os.path.basename(filepath)
    file_extension = filename.rsplit('.', 1)[1].lower()

    print(f"Starting OCR processing for {filename}...")

    if file_extension in ['jpg', 'jpeg', 'png']:
        try:
            img = Image.open(filepath)
            processed_img = preprocess_image(img) 
            text = pytesseract.image_to_string(processed_img, config=TESSERACT_CONFIG)
            extracted_texts.append(text)
            print("Successfully extracted text from single image.")
        except Exception as e:
            print(f"Error processing single image OCR: {e}")
            
    elif file_extension == 'pdf':
        try:
            images = convert_from_path(filepath, dpi=300) 
            
            for i, img in enumerate(images):
                print(f"Processing page {i+1} of PDF...")
                processed_img = preprocess_image(img) 
                text = pytesseract.image_to_string(processed_img, config=TESSERACT_CONFIG)
                extracted_texts.append(text)
                
            print(f"Successfully extracted text from {len(images)} PDF pages.")
        except Exception as e:
            print(f"Error processing PDF OCR (Using system Tesseract which may fail on PDFs): {e}")

    for i, text in enumerate(extracted_texts):
        print(f"--- RAW TEXT (Card {i+1}) ---")
        if text.strip():
            print(text.strip())
        else:
            print("[(No text extracted, please verify card image clarity)]")
        print("------------------------------")

    return extracted_texts


# --- OAUTH FLOW SETUP (Unchanged) ---
def get_google_flow():
    """Initializes the OAuth 2.0 flow object."""
    return Flow.from_client_config(
        client_config={
            'web': {
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'redirect_uris': [GOOGLE_REDIRECT_URI],
            }
        },
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )

def create_google_contact(credentials, contact_data):
    """Uses the Google People API to create a new contact."""
    try:
        service = build('people', 'v1', credentials=credentials)
        
        contact_resource = {
            'names': [{'givenName': contact_data.get('Name', 'Unknown Name')}],
            'emailAddresses': [{'value': contact_data['Email']}] if contact_data.get('Email') else [],
            'phoneNumbers': [{'value': contact_data['Phone']}] if contact_data.get('Phone') else [],
            'organizations': [{
                'name': contact_data.get('Company', ''),
                'title': contact_data.get('Designation', '')
            }] if contact_data.get('Company') else [],
            'addresses': [{'formattedType': 'Work', 'formattedValue': contact_data.get('Address', '')}] if contact_data.get('Address') else [],
            'userDefined': [{'key': 'Website', 'value': contact_data.get('Website', '')}]
        }
        
        if not contact_resource['names'][0]['givenName']:
             contact_resource['names'][0]['givenName'] = contact_data['Email'].split('@')[0] if contact_data['Email'] else 'New Contact'

        service.people().createContact(body=contact_resource).execute()
        return True
    except Exception as e:
        print(f"Error creating Google Contact: {e}")
        return False


# --- FLASK ROUTES (Unchanged) ---

@app.route('/', methods=['GET'])
def index():
    cards = session.pop('processed_card', None)
    status_message = session.pop('status_message', None)
    return render_template('index.html', cards=cards, status_message=status_message)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']

    if file.filename == '':
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        file.save(filepath)
        
        raw_texts = process_ocr(filepath)
        
        structured_data = []
        for raw_text in raw_texts:
            contact_data = generate_structured_data_via_ai(raw_text)
            structured_data.append(contact_data)
            
        print(f"Successfully structured {len(structured_data)} contacts.")
        
        session['processed_card'] = structured_data
        
        try:
            os.remove(filepath)
            print(f"Cleaned up temporary file: {filepath}")
        except OSError as e:
            print(f"Error deleting temporary file: {e}")

        return redirect(url_for('index'))

    print("Error: File type not allowed.")
    return redirect(url_for('index'))


@app.route('/export', methods=['POST'])
def export_data():
    data_to_export = request.get_json(force=True)
    
    if not data_to_export:
        return {"error": "No data received for export."}, 400
    
    df = pd.DataFrame(data_to_export)
    export_columns = ['Name', 'Designation', 'Company', 'Phone', 'Email', 'Address', 'Website']
    df_export = df[export_columns]

    buffer = io.StringIO()
    df_export.to_csv(buffer, index=False, encoding='utf-8')
    buffer.seek(0)
    
    return send_file(
        io.BytesIO(buffer.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='CardScan_Export.csv'
    )

@app.route('/sync/google', methods=['POST'])
def sync_google():
    data = request.get_json(force=True)
    
    if not data:
        session['status_message'] = "Error: No contacts selected for sync."
        return redirect(url_for('index'))
        
    session['contacts_to_sync'] = data
    
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or not GOOGLE_REDIRECT_URI:
        session['status_message'] = "Error: Google Sync credentials missing from server configuration."
        return jsonify({'error': "Server not configured for Google Sync."}), 500


    flow = get_google_flow()
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    session['oauth_state'] = state
    
    return jsonify({'redirect': authorization_url})


@app.route('/oauth2callback')
def oauth2callback():
    if 'oauth_state' not in session or session['oauth_state'] != request.args.get('state'):
        session['status_message'] = "Error: Invalid state parameter during OAuth flow (possible CSRF attempt)."
        return redirect(url_for('index'))

    if 'code' not in request.args:
        session['status_message'] = "Error: Google did not return an authorization code."
        return redirect(url_for('index'))

    flow = get_google_flow()
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    contacts_to_sync = session.pop('contacts_to_sync', [])
    
    sync_count = 0
    fail_count = 0
    
    for contact in contacts_to_sync:
        if create_google_contact(credentials, contact):
            sync_count += 1
        else:
            fail_count += 1
            
    session['status_message'] = f"Successfully synced {sync_count} contacts to Google. ({fail_count} failed)."
    return redirect(url_for('index'))


if __name__ == '__main__':
    # This is the standard best-practice way to run a production-ready Flask app 
    # locally for final testing BEFORE pushing to Render.
    # We use '0.0.0.0' to ensure it binds correctly if Gunicorn were to run it, 
    # but when run directly, it defaults to the Flask dev server.
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        print("\n!!! WARNING: Google OAuth credentials missing from .env. Sync feature will fail. !!!\n")
    
    # We remove debug=True for production simulation, but we'll re-add it for 
    # local testing convenience if you prefer. For true deployment, Gunicorn 
    # handles debug status.
    print("\n--- Running App Locally (Use Gunicorn for production) ---\n")
    app.run(host='0.0.0.0', port=5000)