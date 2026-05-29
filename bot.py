import os
import re
import requests

# Securely pulls your webhook from GitHub Secrets
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

# The 4 reliable stores
STORES = {
    "JB Hi-Fi": "https://www.jbhifi.com.au/search?query=pokemon%20tcg&sortBy=published_at_desc",
    "Kmart": "https://www.kmart.com.au/search/?searchTerm=pokemon%20tcg&sortBy=newest&f.Shops=Kmart&f.Shops=Target",
    "Big W": "https://www.bigw.com.au/toys/trading-cards/pokemon-trading-cards/c/681510201?sort=new",
    "Target": "https://www.target.com.au/search?text=pokemon+tcg&page=1&sortBy=onlinedate&sortOrder=descending"
}

# Items containing these words will be dropped automatically
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

def main():
    seen_items = load_seen_items()
    new_items_found = False

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for store, url in STORES.items():
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            # STRICT REGEX: Only extracts clean, human-readable text. Ignores URL code and JSON.
            matches = re.findall(r'(?i)(?:pokemon|pokémon)[a-zA-Z0-9\s\-\:\'\&\.\(\)]{5,80}', response.text)
            products = set(matches)
            
            for product in products:
                product_lower = product.lower()
                
                # 1. ALLOWLIST: Discards Magic, One Piece, Dragon Ball
                if "pokemon" not in product_lower and "pokémon" not in product_lower:
                    continue
                
                # 2. BLOCKLIST: Discards accessories
                if any(blocked in product_lower for blocked in BLOCKLIST):
                    continue
                
                # 3. MEMORY CHECK: Only triggers alerts for completely unseen listings
                if product not in seen_items:
                    send_discord_alert(store, product, url)
                    seen_items.add(product)
                    new_items_found = True

        except Exception as e:
            print(f"Skipping {store} due to a connection error.")

    if new_items_found:
        save_seen_items(seen_items)

if __name__ == "__main__":
    main
