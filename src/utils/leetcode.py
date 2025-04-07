import json

import requests

LEETCODE_API_ENDPOINT = "https://leetcode.com/graphql"
DAILY_CODING_CHALLENGE_QUERY = """
query questionOfToday {
    activeDailyCodingChallengeQuestion {
        date
        userStatus
        link
        question {
            acRate
            difficulty
            freqBar
            frontendQuestionId: questionFrontendId
            isFavor
            paidOnly: isPaidOnly
            status
            title
            titleSlug
            hasVideoSolution
            hasSolution
            topicTags {
                name
                id
                slug
            }
        }
    }
}
"""


def get_daily_leetcode_question_via_api():
    """Fetches the daily LeetCode question using the GraphQL API."""
    try:
        headers = {"Content-Type": "application/json"}
        payload = {"query": DAILY_CODING_CHALLENGE_QUERY}
        response = requests.post(LEETCODE_API_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes

        data = response.json()

        if "data" in data and "activeDailyCodingChallengeQuestion" in data["data"]:
            daily_question = data["data"]["activeDailyCodingChallengeQuestion"]
            date = daily_question["date"]
            link = "https://leetcode.com" + daily_question["link"]
            title = daily_question["question"]["title"]
            difficulty = daily_question["question"]["difficulty"]
            frontend_id = daily_question["question"]["frontendQuestionId"]

            return {
                "date": date,
                "title": title,
                "link": link,
                "difficulty": difficulty,
                "question_id": frontend_id,
            }, None
        else:
            return None, "Could not find the daily question in the API response."

    except requests.exceptions.RequestException as e:
        return None, f"Error fetching from LeetCode API: {e}"
    except json.JSONDecodeError as e:
        return None, f"Error decoding JSON response: {e}"
    except Exception as e:
        return None, f"An unexpected error occurred: {e}"


if __name__ == "__main__":
    daily_question_info, error = get_daily_leetcode_question_via_api()
    if daily_question_info:
        print("Today's LeetCode Daily Question (via API):")
        print(f"Date: {daily_question_info['date']}")
        print(f"Title: {daily_question_info['title']}")
        print(f"Link: {daily_question_info['link']}")
        print(f"Difficulty: {daily_question_info['difficulty']}")
        print(f"Question ID: {daily_question_info['question_id']}")
    else:
        print(f"Failed to get the daily question: {error}")
