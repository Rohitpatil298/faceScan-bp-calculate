#!/usr/bin/env python3
"""
rPPG Vital Signs Estimation System — Main Entry Point
======================================================
Launches the FastAPI backend with Uvicorn.
Run with:  python main.py

⚠️  DISCLAIMER: This is a WELLNESS ESTIMATION tool, NOT a medical device.
    All readings (HR, HRV, Blood Pressure, Stress) are ESTIMATES derived
    from remote photoplethysmography (rPPG) and lightweight ML models.
    Do NOT use these readings for clinical diagnosis or treatment decisions.
    Consult a qualified healthcare professional for medical advice.
"""

import uvicorn
from api.app import create_app

if __name__ == "__main__":
    app = create_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
