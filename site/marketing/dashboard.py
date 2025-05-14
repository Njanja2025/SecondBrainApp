"""
Social Media Dashboard for monitoring posts and analytics
"""

from flask import Flask, render_template, jsonify, request, send_file
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from voice_generator import VoiceGenerator

app = Flask(__name__)


class SocialMediaDashboard:
    def __init__(self):
        """Initialize the dashboard."""
        self.config_path = "site/marketing/social_media_config.json"
        self.posts_path = "site/marketing/social_posts.json"
        self.analytics_path = "site/marketing/analytics.json"
        self.voice_generator = VoiceGenerator()
        self.load_data()

    def load_data(self):
        """Load configuration and analytics data."""
        try:
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
            with open(self.posts_path, "r") as f:
                self.posts = json.load(f)
            if os.path.exists(self.analytics_path):
                with open(self.analytics_path, "r") as f:
                    self.analytics = json.load(f)
            else:
                self.analytics = {}
        except Exception as e:
            print(f"Error loading data: {e}")
            self.config = {}
            self.posts = {}
            self.analytics = {}

    def get_platform_stats(self):
        """Get statistics for each platform."""
        stats = {}
        for platform in ["linkedin", "twitter", "tiktok"]:
            platform_analytics = self.analytics.get(platform, {})
            stats[platform] = {
                "total_posts": len(platform_analytics),
                "engagement_rate": self.calculate_engagement_rate(platform),
                "reach": self.calculate_reach(platform),
                "impressions": self.calculate_impressions(platform),
                "audio_content": self.get_audio_content(platform),
            }
        return stats

    def get_audio_content(self, platform: str) -> list:
        """Get audio content for a platform."""
        audio_dir = "site/marketing/assets/audio"
        if not os.path.exists(audio_dir):
            return []

        platform_audio = []
        for file in os.listdir(audio_dir):
            if file.startswith(f"{platform}_") and file.endswith("_mixed.mp3"):
                platform_audio.append(
                    {
                        "name": file,
                        "path": os.path.join(audio_dir, file),
                        "created": datetime.fromtimestamp(
                            os.path.getctime(os.path.join(audio_dir, file))
                        ).isoformat(),
                    }
                )
        return sorted(platform_audio, key=lambda x: x["created"], reverse=True)

    def calculate_engagement_rate(self, platform):
        """Calculate engagement rate for a platform."""
        platform_analytics = self.analytics.get(platform, {})
        if not platform_analytics:
            return 0

        total_engagement = sum(
            post.get("metrics", {}).get("engagement_rate", 0)
            for post in platform_analytics.values()
        )
        return total_engagement / len(platform_analytics) if platform_analytics else 0

    def calculate_reach(self, platform):
        """Calculate total reach for a platform."""
        platform_analytics = self.analytics.get(platform, {})
        return sum(
            post.get("metrics", {}).get("reach", 0)
            for post in platform_analytics.values()
        )

    def calculate_impressions(self, platform):
        """Calculate total impressions for a platform."""
        platform_analytics = self.analytics.get(platform, {})
        return sum(
            post.get("metrics", {}).get("impressions", 0)
            for post in platform_analytics.values()
        )

    def get_scheduled_posts(self):
        """Get upcoming scheduled posts."""
        scheduled = []
        for platform, posts in self.posts.items():
            for post in posts:
                if "scheduled_time" in post:
                    scheduled.append(
                        {
                            "platform": platform,
                            "content": post.get("content", "")[:100] + "...",
                            "scheduled_time": post["scheduled_time"],
                            "has_audio": bool(post.get("audio_path")),
                        }
                    )
        return sorted(scheduled, key=lambda x: x["scheduled_time"])

    def generate_engagement_chart(self):
        """Generate engagement rate chart."""
        data = []
        for platform in ["linkedin", "twitter", "tiktok"]:
            platform_analytics = self.analytics.get(platform, {})
            for post_id, post_data in platform_analytics.items():
                data.append(
                    {
                        "platform": platform,
                        "engagement_rate": post_data.get("metrics", {}).get(
                            "engagement_rate", 0
                        ),
                        "date": post_data.get("timestamp", ""),
                    }
                )

        df = pd.DataFrame(data)
        fig = px.line(
            df,
            x="date",
            y="engagement_rate",
            color="platform",
            title="Engagement Rate Over Time",
        )
        return fig.to_json()

    def generate_reach_chart(self):
        """Generate reach chart."""
        data = []
        for platform in ["linkedin", "twitter", "tiktok"]:
            platform_analytics = self.analytics.get(platform, {})
            for post_id, post_data in platform_analytics.items():
                data.append(
                    {
                        "platform": platform,
                        "reach": post_data.get("metrics", {}).get("reach", 0),
                        "date": post_data.get("timestamp", ""),
                    }
                )

        df = pd.DataFrame(data)
        fig = px.bar(df, x="date", y="reach", color="platform", title="Reach Over Time")
        return fig.to_json()

    def generate_audio_content(self, platform: str, content: str) -> str:
        """Generate audio content for a post."""
        try:
            return self.voice_generator.generate_social_media_audio(platform, content)
        except Exception as e:
            print(f"Error generating audio: {e}")
            return None


# Initialize dashboard
dashboard = SocialMediaDashboard()


@app.route("/")
def index():
    """Render dashboard home page."""
    return render_template(
        "dashboard.html",
        stats=dashboard.get_platform_stats(),
        scheduled_posts=dashboard.get_scheduled_posts(),
    )


@app.route("/api/stats")
def get_stats():
    """Get platform statistics."""
    return jsonify(dashboard.get_platform_stats())


@app.route("/api/scheduled")
def get_scheduled():
    """Get scheduled posts."""
    return jsonify(dashboard.get_scheduled_posts())


@app.route("/api/charts/engagement")
def get_engagement_chart():
    """Get engagement rate chart data."""
    return dashboard.generate_engagement_chart()


@app.route("/api/charts/reach")
def get_reach_chart():
    """Get reach chart data."""
    return dashboard.generate_reach_chart()


@app.route("/api/audio/generate", methods=["POST"])
def generate_audio():
    """Generate audio content for a post."""
    try:
        data = request.json
        platform = data.get("platform")
        content = data.get("content")

        if not platform or not content:
            return jsonify({"error": "Missing platform or content"}), 400

        audio_path = dashboard.generate_audio_content(platform, content)
        if not audio_path:
            return jsonify({"error": "Failed to generate audio"}), 500

        return jsonify({"success": True, "audio_path": audio_path})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/audio/<path:filename>")
def get_audio(filename):
    """Serve audio files."""
    try:
        return send_file(
            os.path.join("site/marketing/assets/audio", filename), mimetype="audio/mpeg"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
