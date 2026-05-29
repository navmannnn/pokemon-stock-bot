import os
import re
import cloudscraper

# Securely pulls your webhook from GitHub Secrets
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

# All 7 Target Stores with optimal filters applied
STORES = {
    "JB Hi-Fi": "https://www.jbhifi.com.au/search?query=pokemon%20tcg&sortBy=published_at_desc",
    "Kmart": "https://www.kmart.com.au/search/?searchTerm=pokemon%20tcg&sortBy=newest&f.Shops=Kmart&f.Shops=Target",
    "Big W": "https://www.bigw.com.au/toys/trading-cards/pokemon-trading-cards/c/681510201?sort=new",
    "Mr Toys": "https://www.mrtoys.com.au/new-pokemon-tcg-2452",
    "Target": "https://www.target.com.au/search?text=pokemon+tcg&page=1&sortBy=onlinedate&sortOrder=descending",
    "Toymate": "https://toymate.com.au/search-results/?q=pokemon+tcg&sort=creation_date",
    "EB Games": "https://www.ebgames.com.au/search?q=pokemon+tcg&condition=preorder"
}

# Items containing these words will be dropped automatically
BLOCKLIST = ["portfolio", "sleeves", "pages", "deck box", "binder", "album", "protector", "frame", "folder"]

def send_discord_alert(store, product_name, url):
    data = {
        "content": f"🚨 **New Drop at {store}** 🚨\n**{product_name}**\n[Click here to view]({url})"
    }
    # Uses a quick request instance to fire the alert to Discord
    pusher = cloudscraper.create_scraper()
    pusher.post(WEBHOOK_URL, json=data)

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

    # Initialize cloudscraper to mirror a real desktop browser and beat Cloudflare
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

    for store, url in STORES.items():
        try:
            response = scraper.get(url, timeout=15)
            
            # Regex sniper scan: Extracts potential text matches
            matches = re.findall(r'(?i)(?:pokemon|pokémon)[a-zA-Z0-9\s\-\:\'\&\.\(\)]{5,80}', response.text)
            products = set([match.strip() for match in matches])
            
            for product in products:
                product_lower = product.lower()
                
                # 1. STRICT ALLOWLIST: Discards non-Pokemon cards (Magic, One Piece, Dragon Ball)
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
            print(f"Skipping {store} due to a connection drop or protection block.")

    # Save memory state if changes occurred
    if new_items_found:
        save_seen_items(seen_items)

if __name__ == "__main__":
    main()
