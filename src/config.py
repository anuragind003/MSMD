# src/config.py
"""
Configuration management for MSMD-Synthesizer
Handles API keys and settings
"""

import os
from typing import Optional
from dotenv import load_dotenv
load_dotenv()


def get_gemini_api_key() -> Optional[str]:
    """
    Get Gemini API key from environment variable or prompt user.
    
    Returns:
        API key string or None if not available
    """
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("\n" + "="*60)
        print("Gemini API Key Required")
        print("="*60)
        print("To use Gemini AI for building block selection, you need an API key.")
        print("Get your free API key from: https://makersuite.google.com/app/apikey")
        print("\nYou can either:")
        print("1. Set environment variable: export GEMINI_API_KEY='your_key_here'")
        print("2. Enter it now (will not be saved)")
        print("="*60)
        
        try:
            api_key = input("\nEnter Gemini API Key (or press Enter to skip): ").strip()
            if api_key:
                # Set for current session
                os.environ['GEMINI_API_KEY'] = api_key
                print("✓ API key set for this session")
                return api_key
            else:
                print("⚠ Skipping Gemini AI - will use fallback method")
                return None
        except (KeyboardInterrupt, EOFError):
            print("\n⚠ Skipping Gemini AI - will use fallback method")
            return None
    
    return api_key


def check_gemini_available() -> bool:
    """Check if Gemini AI is available (package installed and key configured)."""
    try:
        import google.generativeai as genai
        api_key = get_gemini_api_key()
        if api_key:
            genai.configure(api_key=api_key)
            return True
    except ImportError:
        return False
    except Exception:
        return False
    return False

