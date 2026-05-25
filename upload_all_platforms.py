"""
Multi-Platform Upload Script

Uploads videos to:
- YouTube Shorts
- Instagram Reels
- TikTok
- Facebook Reels

Each platform requires its own API credentials.
"""

import os
from pathlib import Path
import datetime

# Import platform-specific uploaders
from upload_to_youtube import upload_to_youtube
from upload_instagram import upload_to_instagram
from upload_tiktok import upload_to_tiktok
from upload_facebook import upload_to_facebook
from upload_threads import upload_to_threads
from upload_twitter import upload_to_twitter
from upload_vk import upload_to_vk

def main():
    """Upload video to all configured platforms with enhanced error handling."""
    print("\n" + "="*80)
    print("🚀 MULTI-PLATFORM UPLOAD STARTING")
    print("="*80)
    video_file = Path('output/final_video.mp4')
    
    if not video_file.exists():
        print("[upload] ❌ No video found at output/final_video.mp4")
        print("="*80)
        return
    
    # Read story for metadata
    story_file = Path('output/story.txt')
    if story_file.exists():
        story = story_file.read_text(encoding='utf-8')
        # Use first sentence as title
        title_parts = story.split('.')
        title = title_parts[0][:100] if title_parts else "고대 여성들의 역사"
    else:
        title = f"고대 여성들의 역사 - {datetime.date.today()}"
    
    # Platform-specific content
    descriptions = {
        'youtube': f"{story[:150] if len(story) > 150 else story} #여성역사 #고대역사 #역사 #교육",
        'instagram': f"{story[:2200] if len(story) > 2200 else story}\n\n#여성역사 #고대역사 #역사 #교육 #Shorts #Reels",
        'tiktok': f"{story[:2200] if len(story) > 2200 else story} #여성역사 #고대역사 #역사 #교육 #FYP",
        'facebook': f"{story[:63206] if len(story) > 63206 else story}\n\n#여성역사 #고대역사 #역사 #교육",
        'threads': f"{story[:500] if len(story) > 500 else story} #여성역사 #고대역사 #역사 #교육",
        'twitter': f"{story[:280] if len(story) > 280 else story} #여성역사 #고대역사 #역사",
        'vk': f"{story[:220] if len(story) > 220 else story}\n\n#여성역사 #고대역사 #역사 #교육"
    }

    tags = [
        '역사', '고대 여성', '역사적 사실',
        'Shorts', 'Reels', '교육', '문화'
    ]
    
    results = {}
    
    # Upload to YouTube
    if all([
        os.getenv('YT_CLIENT_ID'),
        os.getenv('YT_CLIENT_SECRET'),
        os.getenv('YT_REFRESH_TOKEN')
    ]):
        print("\n" + "="*60)
        print("📺 Uploading to YouTube...")
        print("="*60)
        try:
            result = upload_to_youtube(video_file, title, descriptions['youtube'], tags)
            results['youtube'] = result
            print(f"✅ YouTube: https://youtube.com/shorts/{result['id']}")
        except Exception as e:
            print(f"❌ YouTube failed: {e}")
            results['youtube'] = {'error': str(e)}
    else:
        print("⏭️  Skipping YouTube (credentials not set)")
    
    # Upload to Instagram
    if all([
        os.getenv('IG_ACCESS_TOKEN'),
        os.getenv('IG_USER_ID')
    ]):
        print("\n" + "="*60)
        print("📸 Uploading to Instagram...")
        print("="*60)
        try:
            result = upload_to_instagram(video_file, descriptions['instagram'])
            results['instagram'] = result
            print(f"✅ Instagram: Uploaded successfully")
        except Exception as e:
            print(f"❌ Instagram failed: {e}")
            results['instagram'] = {'error': str(e)}
    else:
        print("⏭️  Skipping Instagram (credentials not set)")
    
    # Upload to TikTok
    if os.getenv('TIKTOK_ACCESS_TOKEN'):
        print("\n" + "="*60)
        print("🎵 Uploading to TikTok...")
        print("="*60)
        try:
            result = upload_to_tiktok(video_file, title, descriptions['tiktok'])
            results['tiktok'] = result
            print(f"✅ TikTok: Uploaded successfully")
        except Exception as e:
            print(f"❌ TikTok failed: {e}")
            results['tiktok'] = {'error': str(e)}
    else:
        print("⏭️  Skipping TikTok (credentials not set)")
    
    # Upload to Facebook
    if all([
        os.getenv('FB_ACCESS_TOKEN'),
        os.getenv('FB_PAGE_ID')
    ]):
        print("\n" + "="*60)
        print("📘 Uploading to Facebook...")
        print("="*60)
        try:
            result = upload_to_facebook(video_file, descriptions['facebook'])
            results['facebook'] = result
            print(f"✅ Facebook: Uploaded successfully")
        except Exception as e:
            print(f"❌ Facebook failed: {e}")
            results['facebook'] = {'error': str(e)}
    else:
        print("⏭️  Skipping Facebook (credentials not set)")
    
    # Upload to Threads
    if all([
        os.getenv('THREADS_ACCESS_TOKEN'),
        os.getenv('THREADS_USER_ID')
    ]):
        print("\n" + "="*60)
        print("🧵 Uploading to Threads...")
        print("="*60)
        try:
            result = upload_to_threads(video_file, descriptions['threads'])
            results['threads'] = result
            print(f"✅ Threads: Uploaded successfully")
        except Exception as e:
            print(f"❌ Threads failed: {e}")
            results['threads'] = {'error': str(e)}
    else:
        print("⏭️  Skipping Threads (credentials not set)")
    
    # Upload to Twitter/X
    if all([
        os.getenv('TWITTER_API_KEY'),
        os.getenv('TWITTER_API_SECRET'),
        os.getenv('TWITTER_ACCESS_TOKEN'),
        os.getenv('TWITTER_ACCESS_SECRET')
    ]):
        print("\n" + "="*60)
        print("🐦 Uploading to Twitter/X...")
        print("="*60)
        try:
            result = upload_to_twitter(video_file, descriptions['twitter'])
            results['twitter'] = result
            print(f"✅ Twitter: Uploaded successfully")
        except Exception as e:
            print(f"❌ Twitter failed: {e}")
            results['twitter'] = {'error': str(e)}
    else:
        print("⏭️  Skipping Twitter (credentials not set)")
    
    # Upload to VK
    if all([
        os.getenv('VK_ACCESS_TOKEN'),
        os.getenv('VK_GROUP_ID')
    ]):
        print("\n" + "="*60)
        print("🔵 Uploading to VK...")
        print("="*60)
        try:
            result = upload_to_vk(video_file, title, descriptions['vk'])
            results['vk'] = result
            print(f"✅ VK: Uploaded successfully")
        except Exception as e:
            print(f"❌ VK failed: {e}")
            results['vk'] = {'error': str(e)}
    else:
        print("⏭️  Skipping VK (credentials not set)")
    
    # Detailed Summary
    print("\n" + "="*80)
    print("📊 MULTI-PLATFORM UPLOAD SUMMARY")
    print("="*80)

    success_count = 0
    total_count = len(results)

    for platform, result in results.items():
        if result and 'error' not in result:
            status = "✅ SUCCESS"
            success_count += 1
            if platform == 'youtube' and result.get('id'):
                print(f"{platform.capitalize():<12}: {status} - https://youtube.com/shorts/{result['id']}")
            else:
                post_id = result.get('id', 'unknown')
                print(f"{platform.capitalize():<12}: {status} - ID: {post_id}")
        else:
            status = "❌ FAILED"
            error_msg = result.get('error', 'Unknown error') if result else 'Not attempted'
            print(f"{platform.capitalize():<12}: {status} - {error_msg}")

    print("="*80)
    print(f"📈 Success Rate: {success_count}/{total_count} platforms")
    print("="*80)

    if success_count > 0:
        print("🎉 Multi-platform upload completed!")
        print("Check your social media accounts to see the published content.")
    else:
        print("⚠️  No platforms were successfully uploaded to.")
        print("Check your API credentials and try again.")

if __name__ == '__main__':
    main()
