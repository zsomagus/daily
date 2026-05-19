# modulok/music_prompt.py
from  modulok import prashna_core, astro_core, varshaphala_tools
def build_music_prompt(text, mood, keywords, symbols):
    prompt = (
        f"Create an instrumental ambient chillout track inspired by this dream.\n"
        f"Dream: {text}\n"
        f"Mood: {mood}\n"
        f"Keywords: {keywords}\n"
    )
    if symbols:
        prompt += f"Symbols: {', '.join(symbols)}\n"

    prompt += (
        "The music should be atmospheric, soft, flowing, meditative, with warm pads, "
        "airy textures, subtle rhythms, and emotional depth."
    )
    return prompt