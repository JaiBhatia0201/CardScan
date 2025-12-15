#!/usr/bin/env bash

    # 1. Install System Dependencies (Tesseract OCR and Poppler utilities)
    # We use non-interactive mode (-y) and ensure system updates run first.
    echo "--- Installing System Dependencies (Tesseract and Poppler) ---"
    apt-get update -y
    apt-get install -y tesseract-ocr poppler-utils

    # 2. Install Python Dependencies
    echo "--- Installing Python Dependencies ---"
    pip install -r requirements.txt