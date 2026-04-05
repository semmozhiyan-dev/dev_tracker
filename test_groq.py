#!/usr/bin/env python
"""Test Groq integration"""

try:
    from groq import Groq
    print("✓ Groq imported successfully")
except ImportError as e:
    print(f"✗ Failed to import Groq: {e}")
    exit(1)

try:
    from app.config import GROQ_API_KEY
    print(f"✓ Config loaded. API Key present: {bool(GROQ_API_KEY)}")
except Exception as e:
    print(f"✗ Failed to load config: {e}")
    exit(1)

if GROQ_API_KEY:
    try:
        print("Creating Groq client...")
        client = Groq(api_key=GROQ_API_KEY)
        print("✓ Groq client created successfully")
        print(f"Client type: {type(client)}")
        print("Ready for API calls!")
    except Exception as e:
        print(f"✗ Error creating client: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
else:
    print("✗ GROQ_API_KEY is not set")

