import httpx
from database import leetcode_stats
import json

LEETCODE_GRAPHQL = "https://leetcode.com/graphql"

QUERY = """
query getUserProfile($username: String!) {
  matchedUser(username: $username) {
  submissionCalendar
    submitStats {
      acSubmissionNum {
        difficulty
        count
      }
    }
    profile {
      ranking
    }
  }
}
"""

async def fetch_leetcode_stats(leetcode_username: str):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                LEETCODE_GRAPHQL,
                json={
                    "query": QUERY,
                    "variables": {"username": leetcode_username}
                },
                headers={"Content-Type": "application/json"}
            )
            data = response.json()
            user_data = data.get("data", {}).get("matchedUser")
            if user_data is None:
                return None

            stats = user_data["submitStats"]["acSubmissionNum"]
            total = next(s["count"] for s in stats if s["difficulty"] == "All")
            easy = next(s["count"] for s in stats if s["difficulty"] == "Easy")
            medium = next(s["count"] for s in stats if s["difficulty"] == "Medium")
            hard = next(s["count"] for s in stats if s["difficulty"] == "Hard")
            calendar = user_data.get("submissionCalendar", "{}")

            leetcode_stats(leetcode_username, total, easy, medium, hard)

            return {
                "total_solved": total,
                "easy": easy,
                "medium": medium,
                "hard": hard,
                "submission_calendar":calendar
            }
    except Exception:
        return None