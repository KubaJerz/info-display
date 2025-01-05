import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta


class NEWSAPI:
    def __init__(self, type='tech', max_req_per_day=100, no_late_night=True):
        load_dotenv()
        self.api_key = os.getenv("NEWS_API")
        self.type = type
        self.max_req_per_day = max_req_per_day
        self.no_late_night = no_late_night
        self.url = self._get_url()
        self.eastern_tz = timezone(timedelta(hours=-5))
        self.data = []
        self.last_fetch_time = None
        self.rotation = 0  # We pull 10 stories and rotate between 5 and 5

    def _get_url(self):
        """Build the URL for fetching the headlines."""
        base_url = 'https://newsapi.org/v2/top-headlines'
        params = {
            'country': 'us',
            'pageSize': 10,
            'apiKey': self.api_key
        }
        if self.type == 'tech':
            params['category'] = 'technology'
        return f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

    def _is_late_night(self):
        """Check if the current time is considered late night."""
        now = datetime.now(self.eastern_tz)
        return now.hour >= 22 or now.hour <= 4

    def _time_since_last_fetch(self):
        """Calculate the time elapsed since the last fetch."""
        now = datetime.now(self.eastern_tz)
        return now - self.last_fetch_time if self.last_fetch_time else None

    def _should_fetch(self):
        """Determine whether it's time to fetch new stories."""
        time_since_last_fetch = self._time_since_last_fetch()
        if not time_since_last_fetch:
            return True
        if self.no_late_night and self._is_late_night():
            return False
        fetch_interval = timedelta(hours=18) / (self.max_req_per_day - 10)
        if time_since_last_fetch > fetch_interval:
            return True
        return False

    def _fetch_stories(self):
        """Fetch the latest stories from the API."""
        response = requests.get(self.url)
        data = response.json()
        self.data = self._process_stories(data["articles"])
        self.last_fetch_time = datetime.now(self.eastern_tz)

    def _process_stories(self, articles):
        """Process raw API articles into a more usable format."""
        processed_stories = []
        for story in articles:
            dt = datetime.fromisoformat(story['publishedAt'][:-1]).replace(tzinfo=timezone.utc)
            local_time = dt.astimezone(self.eastern_tz)
            processed_stories.append({
                "source": story["source"]["name"],
                "headline": story["title"][:-3 - len(story["source"]["name"])],
                "time": local_time.strftime('%Y-%m-%d %I:%M %p'),
                "body": story["description"]
            })
        return processed_stories

    def get_stories(self):
        """Get a list of stories, rotating between the first and second halves."""
        if self._should_fetch():
            self._fetch_stories()

        mid_point = len(self.data) // 2
        if self.rotation == 0:
            self.rotation = 1
            return self.data[:mid_point]
        else:
            self.rotation = 0
            return self.data[mid_point:]