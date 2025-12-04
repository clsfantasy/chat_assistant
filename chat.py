import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables (for local dev if .env exists)
load_dotenv()

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not found.")
        print("Please set it when running the container: -e GEMINI_API_KEY=your_key")
        return

    try:
        genai.configure(api_key=api_key)
        
        # Try to initialize with preferred models
        # We prioritize these, but will fall back to ANY available 'generateContent' model
        preferred_models = [
            "gemini-2.5-flash", 
        ]
        chat = None
        active_model_name = None

        print("Initializing Gemini API...")

        # 1. Try preferred models first
        for model_name in preferred_models:
            try:
                model = genai.GenerativeModel(model_name)
                model.count_tokens("test") 
                chat = model.start_chat(history=[])
                active_model_name = model_name
                print(f"Successfully connected to preferred model: {active_model_name}")
                break
            except Exception:
                continue

        # 2. If preferred failed, auto-discover from account's available models
        if not chat:
            print("Preferred models failed. Scanning your account for available models...")
            try:
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        try:
                            # Try to connect to this discovered model
                            print(f"Trying discovered model: {m.name}...")
                            model = genai.GenerativeModel(m.name)
                            model.count_tokens("test")
                            chat = model.start_chat(history=[])
                            active_model_name = m.name
                            print(f"Successfully connected to: {active_model_name}")
                            break
                        except Exception:
                            continue
            except Exception as e:
                print(f"Error listing models: {e}")

        if not chat:
            print("\nCRITICAL ERROR: Could not connect to ANY Gemini model.")
            print("Please check your API Key permissions, billing status, and network connection.")
            print("Your API Key might be invalid or lacks access to Generative Language API.")
            return

        print("--- Gemini AI Chat Assistant ---")
        print(f"Using model: {active_model_name}")
        print("Type 'quit', 'exit', or 'bye' to end the session.")
        print("--------------------------------")

        while True:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nGoodbye!")
                break

            try:
                response = chat.send_message(user_input)
                print(f"Gemini: {response.text}")
            except Exception as e:
                print(f"An error occurred: {e}")

    except Exception as e:
        print(f"Failed to initialize Gemini API: {e}")

if __name__ == "__main__":
    main()
