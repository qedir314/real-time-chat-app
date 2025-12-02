import os
import httpx
from typing import Optional

# Try to load .env file for local development (optional, Docker uses env vars directly)
try:
    from dotenv import load_dotenv
    from pathlib import Path
    env_path = Path(__file__).resolve().parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # dotenv not installed, will use system env vars


class AIBot:
    """
    AI Chatbot integration using Google Gemini API.
    Responds to messages starting with /bot or containing @ai
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        self.enabled = bool(self.api_key)
        if self.enabled:
            print(f"✓ AI Bot initialized with API key: {self.api_key[:10]}...")
        else:
            print("✗ AI Bot disabled - no GEMINI_API_KEY found")

    def should_respond(self, message: str) -> bool:
        """Check if bot should respond to this message"""
        if not self.enabled:
            return False
        msg_lower = message.lower().strip()
        return msg_lower.startswith("/bot") or "@ai" in msg_lower

    async def get_response(self, message: str, username: str) -> Optional[str]:
        """Get AI response for the message"""
        if not self.enabled:
            print("Bot not enabled - API key missing")
            return None

        # Clean the message - remove /bot or @ai prefix
        clean_message = message.strip()
        if clean_message.lower().startswith("/bot"):
            clean_message = clean_message[4:].strip()
        clean_message = clean_message.replace("@ai", "").replace("@AI", "").strip()

        if not clean_message:
            return "Hello! How can I help you?"

        print(f"AI Bot processing: '{clean_message}' from {username}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    # CRITICAL: This sets the persona properly
                    "systemInstruction": {
                        "parts": [{
                            "text": "You are a friendly, casual AI assistant in a group chat. "
                                    "Always respond concisely (max 100 words), helpfully, and fun. "
                                    "Answer questions directly, even opinions or facts about people."
                        }]
                    },
                    "contents": [
                        {
                            "role": "user",  # Explicitly mark as user input
                            "parts": [{"text": f"{username} asked: {clean_message}"}]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 200,
                    }
                }

                print(f"Sending request to Gemini API...")
                response = await client.post(
                    f"{self.api_url}?key={self.api_key}",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                print(f"Gemini API response status: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    try:
                        text = result["candidates"][0]["content"]["parts"][0]["text"]
                        print(f"AI Bot response generated: {len(text)} characters")
                        return text.strip()
                    except (KeyError, IndexError) as e:
                        print(f"Error parsing response: {e}")
                        print(f"Response structure: {result}")
                        return "I'm having trouble understanding. Could you rephrase that?"
                else:
                    error_msg = f"Gemini API error: {response.status_code} - {response.text}"
                    print(error_msg)
                    return f"Sorry, I encountered an error. Please try again later."

        except httpx.TimeoutException:
            print("Gemini API timeout")
            return "Sorry, I'm taking too long to respond. Please try again."
        except Exception as e:
            print(f"Error calling Gemini API: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return f"Sorry, I encountered an error: {type(e).__name__}"


# Singleton instance
ai_bot = AIBot()

