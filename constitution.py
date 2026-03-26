# constitution.py - Constitutional filters for LROS

META_KEYWORDS = [
    "how do you work",
    "what are your layers",
    "prompt", 
    "system prompt",
    "are you ai",
    "who created you",
    "what is lros",
    "how are you built"
]

def is_meta_question(text):
    text_lower = text.lower()
    for keyword in META_KEYWORDS:
        if keyword in text_lower:
            return True
    return False

def get_constitutional_response():
    return "I'm here to assist with your operational needs. Please ask about your business tasks."