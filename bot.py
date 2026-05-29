import os
import re
import requests
import urllib.parse

# Securely pulls your webhook from GitHub Secrets
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

# Sticking to JB Hi-Fi since it doesn't hard-block GitHub servers
STORES = {
    "JB Hi-Fi": "https://www.jbhifi.com.au/search?query=pokemon%20tcg&sortBy=published_at_desc"
}

BLOCKLIST = ["portfolio", "sleeves", "pages", "deck box", "binder", "album", "protector", "frame", "folder"]

def send_discord_alert(store, product_name, url):
    data = {
        "content": f"🚨 **New Drop at {store}** 🚨\n**{product_name.strip()}**\n[Click here to view]({url})"
    }
    requests.post(WEBHOOK_URL, json=data)

def load_seen_items():
    if os.path.exists("seen_items.txt"):
        with open("seen_items.txt", "r", encoding="utf-8") as f:
            return set(f.read().splitlines())
    return set()

def save_seen_items(seen_items):
    with open("seen_items.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(seen_items))

def clean_product_name(raw_text):
    # Decodes URL characters like %22 into "
    decoded = urllib.parse.unquote(raw_text)
    # Strips out any leftover JSON/HTML junk codes
    cleaned = re.sub(r'[^a-zA-Z0-9\s\-\:\'\&\.\(\)]', '', decoded)
    # Removes words like 'name' or 'title' if they got caught in the crossfire
    cleaned = re.sub(r'\b(name|title|product|displayName)\b', '', cleaned, flags=re.IGNORECASE)
    return ' '.join(cleaned.split())

def main():
    seen_items = load_seen_items()
    new_items_found = False

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for store, url in STORES.items():
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            # Grabs the text around the pokemon keywords inside the raw JSON code
            matches = re.findall(r'(?i)(?:pokemon|pokémon)[^"<\\]{10,70}', response.text)
            
            for raw_match in set(matches):
                product = clean_product_name(raw_match)
                product_lower = product.lower()
                
                # Verify it's a valid title length after cleaning
                if len(product) < 10 or len(product) > 80:
                    continue
                
                # 1. ALLOWLIST
                if "pokemon" not in product_lower and "pokémon" not in product_lower:
                    continue
                
                # 2. BLOCKLIST
                if any(blocked in product_lower for blocked in BLOCKLIST):
                    continue
                
                # 3. MEMORY CHECK
                if product not in seen_items:
                    send_discord_alert(store, product, url)
                    seen_items.add(product)
                    new_items_found = True

        except Exception as e:
            print(f"Skipping {store} due to an error.")

    if new_items_found:
        save_seen_items(seen_items)

if __name__ == "__main__":
    main()
