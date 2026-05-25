"""
Generate new topics using AI when topics.txt runs low.

This script:
1. Checks if topics.txt has enough topics (< 50 remaining)
2. Generates 100 new unique topics using Pollinations AI
3. Appends them to topics.txt
"""

import requests
from urllib.parse import quote
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def generate_new_topics(count=100):
    """Generate new Korean topics about ancient women using paid Pollinations API."""
    
    api_key = os.getenv("POLLINATIONS_API_KEY")
    if not api_key:
        raise ValueError("POLLINATIONS_API_KEY environment variable is required for paid API")
    
    system_prompt = (
        "당신은 고대 문명의 여성 역사를 전문으로 하는 역사학자입니다. "
        f"한국어로 {count}개의 고유한 주제 목록을 만드세요. "
        "각 주제는 짧고(5-10단어), 흥미롭고 교육적이어야 합니다. "
        "주제는 법률, 관습, 유명한 여성, 직업, 종교, 문화, 예술을 다루어야 합니다. "
        "주제만을 한 줄에 하나씩 번호나 표시 없이 출력하세요."
    )
    
    user_prompt = f"고대 문명의 여성들에 대한 {count}개의 고유한 주제를 만들어주세요"
    
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
    
    print(f"[topics] Generating {count} new Korean topics via paid API...")
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    
    response_data = r.json()
    text = response_data['choices'][0]['message']['content'].strip()
    
    # Parse topics
    topics = []
    for line in text.split('\n'):
        # Remove numbering and clean
        cleaned = line.strip()
        # Remove common prefixes
        for prefix in ['- ', '* ', '• ']:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
        # Remove numbering like "1. " or "1) "
        import re
        cleaned = re.sub(r'^\d+[\.\:\)]\s*', '', cleaned)
        
        if cleaned and len(cleaned) > 5:
            topics.append(cleaned)
    
    return topics[:count]

def check_and_update_topics():
    """Check topics.txt and add more if needed."""
    
    topics_file = Path('topics.txt')
    
    # Read existing topics
    if topics_file.exists():
        with open(topics_file, 'r', encoding='utf-8') as f:
            existing_topics = [line.strip() for line in f if line.strip()]
    else:
        existing_topics = []
    
    print(f"[topics] Current topics: {len(existing_topics)}")
    
    # Check if we need more topics (trigger at 500 instead of 50)
    if len(existing_topics) < 500:
        print(f"[topics] Low on topics! Generating 100 more...")
        
        new_topics = generate_new_topics(100)
        
        # Append to file
        with open(topics_file, 'a', encoding='utf-8') as f:
            for topic in new_topics:
                f.write(f"{topic}\n")
        
        print(f"[topics] Added {len(new_topics)} new Korean topics!")
        print(f"[topics] Total topics now: {len(existing_topics) + len(new_topics)}")
    else:
        print(f"[topics] Enough topics available ({len(existing_topics)})")

if __name__ == '__main__':
    check_and_update_topics()
