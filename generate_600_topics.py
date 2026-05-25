"""
Generate 600 Portuguese topics about ancient women's history.
"""

import requests
from urllib.parse import quote
from pathlib import Path
import time

def generate_batch(batch_num, count=100):
    """Generate a batch of Korean topics using paid Pollinations API."""
    
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("POLLINATIONS_API_KEY")
    
    system_prompt = (
        "You are a historian specialized in ancient women's history. "
        f"Create {count} unique topics in Korean about women in ancient civilizations. "
        "Each topic should be 5-10 words, interesting and educational. "
        "Cover: laws, customs, famous women, professions, religion, culture, art. "
        "Output ONLY the topics, one per line, no numbers or bullets."
    )
    
    user_prompt = f"Generate {count} unique Korean topics about women in ancient civilizations"
    
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.9
    }
    
    print(f"[batch {batch_num}] Generating {count} Korean topics via paid API...")
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        
        response_data = r.json()
        text = response_data['choices'][0]['message']['content'].strip()
        
        # Parse topics
        topics = []
        for line in text.split('\n'):
            cleaned = line.strip()
            # Remove common prefixes
            for prefix in ['- ', '* ', '• ', '→ ', '> ']:
                if cleaned.startswith(prefix):
                    cleaned = cleaned[len(prefix):]
            # Remove numbering
            import re
            cleaned = re.sub(r'^\d+[\.\:\)\-]\s*', '', cleaned)
            
            if cleaned and len(cleaned) > 5:
                topics.append(cleaned)
        
        print(f"[batch {batch_num}] Generated {len(topics)} topics")
        return topics[:count]
    
    except Exception as e:
        print(f"[batch {batch_num}] Error: {e}")
        return []

def main():
    """Generate 600 Portuguese topics in batches."""
    
    all_topics = []
    batches = 6  # 6 batches of 100 = 600 topics
    
    for i in range(batches):
        topics = generate_batch(i+1, 100)
        all_topics.extend(topics)
        
        print(f"[progress] Total topics so far: {len(all_topics)}")
        
        # Wait between batches to avoid rate limits
        if i < batches - 1:
            print("[progress] Waiting 5 seconds before next batch...")
            time.sleep(5)
    
    # Write to file
    topics_file = Path('topics.txt')
    with open(topics_file, 'w', encoding='utf-8') as f:
        for topic in all_topics:
            f.write(f"{topic}\n")
    
    print(f"\n[done] Generated {len(all_topics)} Portuguese topics!")
    print(f"[done] Saved to {topics_file}")

if __name__ == '__main__':
    main()
