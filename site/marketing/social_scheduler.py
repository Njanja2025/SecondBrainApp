"""
Automated social media posting scheduler with platform integrations and analytics
"""
import os
import json
import logging
import schedule
import time
import requests
import pytz
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SocialMediaScheduler:
    def __init__(self, config_path: str = "site/marketing/social_media_config.json"):
        """Initialize the social media scheduler."""
        self.config_path = config_path
        self.config = self.load_config()
        self.posts = self.load_posts()
        self.schedule = {}
        self.analytics = {}
        
    def load_config(self) -> dict:
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
            
    def load_posts(self) -> dict:
        """Load social media posts from configuration."""
        try:
            with open("site/marketing/social_posts.json", 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load posts: {e}")
            raise
            
    def send_notification(self, subject: str, message: str):
        """Send email notification."""
        try:
            email_config = self.config.get('scheduling', {}).get('notification_email')
            if not email_config:
                return
                
            msg = MIMEMultipart()
            msg['From'] = email_config
            msg['To'] = email_config
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            # TODO: Configure SMTP settings
            # server = smtplib.SMTP('smtp.gmail.com', 587)
            # server.starttls()
            # server.login(email_config, 'your-password')
            # server.send_message(msg)
            # server.quit()
            
            logger.info(f"Notification sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            
    def post_to_linkedin(self, post: dict) -> bool:
        """Post content to LinkedIn."""
        try:
            config = self.config.get('linkedin', {})
            headers = {
                'Authorization': f'Bearer {config.get("access_token")}',
                'Content-Type': 'application/json'
            }
            
            # Prepare post data
            post_data = {
                'author': f'urn:li:person:{config.get("client_id")}',
                'lifecycleState': 'PUBLISHED',
                'specificContent': {
                    'com.linkedin.ugc.ShareContent': {
                        'shareCommentary': {
                            'text': post.get('content', '')
                        },
                        'shareMediaCategory': 'NONE'
                    }
                },
                'visibility': {
                    'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'
                }
            }
            
            # Make API request
            response = requests.post(
                'https://api.linkedin.com/v2/ugcPosts',
                headers=headers,
                json=post_data
            )
            
            if response.status_code == 201:
                logger.info("Successfully posted to LinkedIn")
                self.track_analytics('linkedin', post, response.json())
                return True
            else:
                logger.error(f"Failed to post to LinkedIn: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to post to LinkedIn: {e}")
            return False
            
    def post_to_twitter(self, post: dict) -> bool:
        """Post content to Twitter."""
        try:
            config = self.config.get('twitter', {})
            headers = {
                'Authorization': f'Bearer {config.get("access_token")}',
                'Content-Type': 'application/json'
            }
            
            # Prepare post data
            post_data = {
                'text': post.get('content', '')
            }
            
            # Make API request
            response = requests.post(
                'https://api.twitter.com/2/tweets',
                headers=headers,
                json=post_data
            )
            
            if response.status_code == 201:
                logger.info("Successfully posted to Twitter")
                self.track_analytics('twitter', post, response.json())
                return True
            else:
                logger.error(f"Failed to post to Twitter: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to post to Twitter: {e}")
            return False
            
    def post_to_tiktok(self, post: dict) -> bool:
        """Post content to TikTok."""
        try:
            config = self.config.get('tiktok', {})
            headers = {
                'Authorization': f'Bearer {config.get("access_token")}',
                'Content-Type': 'application/json'
            }
            
            # Prepare post data
            post_data = {
                'text': post.get('content', '')
            }
            
            # Make API request
            response = requests.post(
                'https://open.tiktokapis.com/v2/post/publish/text/',
                headers=headers,
                json=post_data
            )
            
            if response.status_code == 200:
                logger.info("Successfully posted to TikTok")
                self.track_analytics('tiktok', post, response.json())
                return True
            else:
                logger.error(f"Failed to post to TikTok: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to post to TikTok: {e}")
            return False
            
    def track_analytics(self, platform: str, post: dict, response: dict):
        """Track post analytics."""
        try:
            if not self.config.get('analytics', {}).get('tracking_enabled'):
                return
                
            metrics = self.config.get('analytics', {}).get('metrics', [])
            
            # Initialize platform analytics if not exists
            if platform not in self.analytics:
                self.analytics[platform] = {}
                
            # Track basic metrics
            self.analytics[platform][post.get('id', '')] = {
                'timestamp': datetime.now().isoformat(),
                'post_id': response.get('id'),
                'metrics': {
                    metric: 0 for metric in metrics
                }
            }
            
            # TODO: Implement actual analytics tracking
            # This would involve making API calls to each platform's analytics endpoints
            
        except Exception as e:
            logger.error(f"Failed to track analytics: {e}")
            
    def schedule_post(self, platform: str, post: dict, post_time: datetime):
        """Schedule a post for a specific platform."""
        try:
            # Add post to schedule
            if platform not in self.schedule:
                self.schedule[platform] = []
                
            # Get platform-specific schedule
            platform_config = self.config.get(platform, {}).get('posting_schedule', {})
            preferred_times = platform_config.get('preferred_times', [])
            
            # Adjust post time to nearest preferred time
            if preferred_times:
                post_time = self.adjust_to_preferred_time(post_time, preferred_times)
                
            self.schedule[platform].append({
                'post': post,
                'time': post_time
            })
            
            logger.info(f"Scheduled {platform} post for {post_time}")
            
        except Exception as e:
            logger.error(f"Failed to schedule post: {e}")
            raise
            
    def adjust_to_preferred_time(self, post_time: datetime, preferred_times: List[str]) -> datetime:
        """Adjust post time to nearest preferred time."""
        try:
            # Convert preferred times to datetime objects
            preferred_datetimes = []
            for time_str in preferred_times:
                hour, minute = map(int, time_str.split(':'))
                preferred_time = post_time.replace(hour=hour, minute=minute)
                preferred_datetimes.append(preferred_time)
                
            # Find nearest preferred time
            nearest_time = min(preferred_datetimes, key=lambda x: abs(x - post_time))
            return nearest_time
            
        except Exception as e:
            logger.error(f"Failed to adjust post time: {e}")
            return post_time
            
    def create_post_schedule(self):
        """Create a posting schedule for the next 30 days."""
        try:
            # Get current time
            now = datetime.now()
            
            # Schedule LinkedIn posts (3 times per week)
            linkedin_posts = self.posts.get('linkedin', [])
            for i, post in enumerate(linkedin_posts):
                post_time = now + timedelta(days=i*2)  # Every other day
                self.schedule_post('linkedin', post, post_time)
                
            # Schedule Twitter posts (daily)
            twitter_posts = self.posts.get('twitter', [])
            for i, post in enumerate(twitter_posts):
                post_time = now + timedelta(days=i)
                self.schedule_post('twitter', post, post_time)
                
            # Schedule TikTok posts (2 times per week)
            tiktok_posts = self.posts.get('tiktok', [])
            for i, post in enumerate(tiktok_posts):
                post_time = now + timedelta(days=i*3)  # Every third day
                self.schedule_post('tiktok', post, post_time)
                
            logger.info("Created posting schedule for next 30 days")
            
        except Exception as e:
            logger.error(f"Failed to create post schedule: {e}")
            raise
            
    def post_to_platform(self, platform: str, post: dict):
        """Post content to a specific platform."""
        try:
            success = False
            retry_count = 0
            max_retries = self.config.get('scheduling', {}).get('max_retry_attempts', 3)
            
            while not success and retry_count < max_retries:
                if platform == 'linkedin':
                    success = self.post_to_linkedin(post)
                elif platform == 'twitter':
                    success = self.post_to_twitter(post)
                elif platform == 'tiktok':
                    success = self.post_to_tiktok(post)
                    
                if not success:
                    retry_count += 1
                    if retry_count < max_retries:
                        time.sleep(60)  # Wait 1 minute before retrying
                        
            if not success:
                self.send_notification(
                    f"Failed to post to {platform}",
                    f"Failed to post after {max_retries} attempts. Post content: {post.get('content', '')[:100]}..."
                )
                
        except Exception as e:
            logger.error(f"Failed to post to {platform}: {e}")
            self.send_notification(
                f"Error posting to {platform}",
                f"An error occurred while posting to {platform}: {str(e)}"
            )
            
    def run_scheduler(self):
        """Run the social media scheduler."""
        try:
            # Create initial schedule
            self.create_post_schedule()
            
            # Schedule posts
            for platform, posts in self.schedule.items():
                for scheduled_post in posts:
                    post_time = scheduled_post['time']
                    post = scheduled_post['post']
                    
                    # Schedule the post
                    schedule.every().day.at(post_time.strftime('%H:%M')).do(
                        self.post_to_platform, platform, post
                    )
                    
            # Run the scheduler
            while True:
                schedule.run_pending()
                time.sleep(60)
                
        except Exception as e:
            logger.error(f"Scheduler failed: {e}")
            self.send_notification(
                "Scheduler Error",
                f"The social media scheduler encountered an error: {str(e)}"
            )
            raise

def main():
    """Run the social media scheduler."""
    try:
        # Initialize scheduler
        scheduler = SocialMediaScheduler()
        
        # Run scheduler
        scheduler.run_scheduler()
        
    except Exception as e:
        logger.error(f"Failed to run scheduler: {e}")
        raise

if __name__ == '__main__':
    main() 