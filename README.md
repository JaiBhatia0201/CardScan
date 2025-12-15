# CardScan – Business Card Manager (MVP)

CardScan is a **Flask-based web application** built as a *purpose-driven personal project* with the long-term goal of evolving into a **commercial-ready product** (web + mobile).

The current version represents the **MVP (Minimum Viable Product)** of the web platform. It focuses on validating the core idea: converting physical business cards into structured, reusable digital contact data using **OCR and AI**, followed by real-world exports and integrations.

This repository exists to:

* Clearly communicate the project vision and capabilities
* Serve as a deployment-ready codebase (Render)
* Act as a technical foundation for future expansion

---

🌐 Live Demo

🔗 Deployed Application [here](https://cardscan-6jbc.onrender.com)

The app is deployed using a Docker-based setup on Render to ensure proper support for OCR and PDF processing dependencies (Tesseract & Poppler).

---

## 🚀 Features

* 📸 **Multiple Input Methods**

  * Upload images (`.jpg`, `.png`) or PDFs
  * Capture cards directly using your phone camera (mobile-friendly)

* 🔍 **OCR Processing**

  * Image preprocessing for better accuracy
  * Text extraction using **Tesseract OCR**

* 🤖 **AI-Powered Data Structuring**

  * Uses **Google Gemini API** to convert raw OCR text into structured fields:

    * Name
    * Designation
    * Company
    * Phone
    * Email
    * Address
    * Website

* ✏️ **Editable Review Table**

  * Review & manually correct extracted data before exporting

* 📤 **Export Options**

  * Export cleaned data to **CSV / Excel**

* 🔗 **Google Contacts Integration**

  * OAuth 2.0 based sync with Google Contacts

---

## 🛠️ Tech Stack

**Backend**

* Python
* Flask
* Gunicorn (production server)

**Frontend**

* HTML (Jinja2 templates)
* Tailwind CSS
* Vanilla JavaScript

**AI & OCR**

* Tesseract OCR
* Google Gemini API (LLM-based parsing)

**Integrations**

* Google People API (Contacts)
* OAuth 2.0

---

## 📂 Project Structure

```
CardScan/
├── app.py
├── requirements.txt
├── uploads/            # Temporary upload storage
├── templates/
│   └── index.html      # Main UI
├── .env                # Environment variables (not committed)
└── README.md
```

---

## ⚙️ Setup & Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/cardscan.git
cd cardscan
```

### 2️⃣ Create & Activate Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Install System Dependencies

**Tesseract OCR**

* Windows: [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
* Linux:

```bash
sudo apt install tesseract-ocr poppler-utils
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
FLASK_SECRET_KEY=your_secret_key

GEMINI_API_KEY=your_gemini_api_key

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:5000/oauth2callback
```

> ⚠️ Without the Gemini API key, the app will still work but **AI structuring will be skipped**.

---

## ▶️ Running the App Locally

```bash
python app.py
```

Open your browser at:

```
http://localhost:5000
```

---

## 🔄 Usage Flow

1. Upload a business card image / PDF **or** capture via camera
2. OCR extracts raw text
3. Gemini AI structures the data
4. Review & edit extracted fields
5. Export to CSV **or** sync to Google Contacts

---

## 📦 Deployment

This project is deployed using **Docker** to ensure reliable availability of required system-level dependencies such as **Tesseract OCR** and **Poppler**.

### Why Docker?

Initial deployment attempts using a standard Python service on Render were unsuccessful due to missing native dependencies required for OCR and PDF processing. Since these dependencies cannot be reliably installed in a plain Python runtime, the project was migrated to a **Docker-based deployment**.

Docker allows full control over the runtime environment and ensures consistent behavior across development and production.

### Docker-Based Deployment (Recommended)

The application uses a custom `Dockerfile` that:
- Uses a slim Python base image
- Installs Tesseract OCR and Poppler utilities
- Installs Python dependencies from `requirements.txt`
- Runs the application using Gunicorn

### Deploying on Render (Docker)

1. Create a new **Web Service** on Render
2. Select **Docker** as the environment
3. Connect the GitHub repository
4. Configure required environment variables in the Render dashboard
5. Deploy — Render automatically builds and runs the container

No additional start command or Procfile configuration is required when using Docker.

> Note: The `Procfile` is retained for non-Docker deployments, but Docker is the recommended and actively used deployment method.

---

## 🧪 Limitations (MVP)

* OCR accuracy depends heavily on image quality
* Multi-page PDF OCR may fail on some cloud environments
* No authentication / user accounts (single-session based)

---

## 🔮 Future Improvements

* User authentication & dashboards
* Better OCR preprocessing (deskewing, denoising)
* Batch processing of multiple cards
* Database persistence
* Card image storage & history
* Mobile-first PWA version

---

## 📜 License

This project is currently maintained as a **personal / proprietary MVP**.

The code is published publicly for:

* Transparency
* Deployment purposes
* Demonstration of technical capability

Reuse, redistribution, or commercial usage should be discussed with the author.

---

## 🙌 Acknowledgements

* Tesseract OCR
* Google Gemini API
* Google People API
* Tailwind CSS

---

⭐ If you found this project helpful or interesting, consider giving it a star!
