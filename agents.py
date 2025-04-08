import os
import smtplib
import time
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from typing import Any, Dict, TypedDict

import schedule
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

from src.utils import leetcode  # Import your LeetCode utility

load_dotenv()

# --- Environment Variables ---
email_sender = os.getenv("EMAIL_SENDER")
email_receiver = os.getenv("EMAIL_RECEIVER")
email_password = os.getenv("EMAIL_PASSWORD")
smtp_server = os.getenv("SMTP_SERVER")
smtp_port = int(os.getenv("SMTP_PORT", 465))
groq_api_key = os.getenv("GROQ_API_KEY")

# --- Initialize Groq LLM and LeetCode API ---
if not groq_api_key:
    raise ValueError("GROQ_API_KEY not found in .env file.")
model = ChatGroq(api_key=groq_api_key, model="llama-3.3-70b-versatile")


# --- State Definition ---
class MonitoringState(TypedDict):
    leetcode_data: Dict
    leetcode_title: str
    leetcode_difficulty: str
    leetcode_title_slug: str
    status: str
    should_send_email: bool
    email_subject: str
    email_body: str
    last_email_time: datetime


# --- Email Sending Function ---
def send_email(subject: str, body: str):
    """Sends an email using the configured Gmail settings."""
    print(
        f"Attempting to send email with subject: '{subject}' to '{email_receiver}'"
    )  # Added logging
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = email_sender
        msg["To"] = email_receiver

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            print("Connecting to SMTP server...")  # Added logging
            server.login(email_sender, email_password)
            print("Successfully logged in to SMTP server.")  # Added logging
            server.sendmail(email_sender, [email_receiver], msg.as_string())
        print(f"Email sent: {subject} to {email_receiver}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


# --- LangGraph Nodes ---
def fetch_leetcode_data(state: MonitoringState) -> Dict:
    """Fetches the daily LeetCode question info."""
    print("Fetching LeetCode data...")
    question_info, error = leetcode.get_daily_leetcode_question_via_api()
    print(question_info)
    if question_info:
        return {
            "leetcode_data": question_info,
            "leetcode_title": question_info["title"],
            "leetcode_difficulty": question_info["difficulty"],
            "status": "open",  # Assuming open initially
        }
    else:
        print(f"Error fetching LeetCode data: {error}")
        return {
            "leetcode_data": {},
            "leetcode_title": "Error",
            "leetcode_difficulty": "Error",
            "status": "error",
        }


def decide_send_email(state: MonitoringState) -> Dict:
    """Decides whether to send an email."""
    print("\n--- Inside decide_send_email ---")
    print(f"Current state: {state}")
    if state["status"] == "solved":
        print("LeetCode problem is solved. No more emails.")
        return {"should_send_email": False}
    elif state["status"] != "open":
        print(f"LeetCode problem status is '{state['status']}'. Not sending emails.")
        return {"should_send_email": False}

    current_time_coimbatore = datetime.now(tz=datetime.now().astimezone().tzinfo)
    last_email = state.get("last_email_time")

    if last_email is None or current_time_coimbatore - last_email >= timedelta(hours=2):
        print("Time elapsed or first run, deciding to send email.")
        return {"should_send_email": True}
    else:
        print("Not enough time has passed since the last email.")
        return {"should_send_email": False}


def generate_email_subject(state: MonitoringState) -> Dict:
    """Generates the email subject with LeetCode title and difficulty."""
    subject = f"LeetCode: {state.get('leetcode_title', 'N/A')} ({state.get('leetcode_difficulty', 'N/A')})"
    return {"email_subject": subject}


prompt_template_body = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an AI assistant that helps draft well-structured and engaging technical emails while ensuring they do not get flagged as spam. "
            "Your task is to craft an email about the LeetCode problem '{leetcode_title}' with difficulty '{leetcode_difficulty}' while maintaining a professional yet conversational tone.\n\n"
            "The email should:\n"
            "- Clearly mention the **LeetCode problem title** and its **difficulty level**.\n"
            "- Explain the **problem statement concisely**, including constraints if necessary Don't Provide any hints and Solution.\n"
            "- Use a **structured format** with short paragraphs, bullet points, and a clear call to action.\n"
            "- Avoid **spam-triggering words/phrases** such as 'ongoing efforts,' 'improve our skills,' 'real-world problems,' and instead use natural, technical language.\n"
            "- Be **personalized and friendly**, avoiding generic mass-email style greetings like 'Dear Fellow Programmers.'\n"
            "- End with a **polite closing and sender details**."
            "- The Sender detail is Agentic AI **.",
        ),
        (
            "human",
            "Write an email body about the LeetCode problem titled '{leetcode_title}' with difficulty '{leetcode_difficulty}'. "
            "Ensure it is a **proper email**, **professional**, and structured in a way that it does not get flagged as spam.",
        ),
    ]
)


def generate_email_body(state: MonitoringState) -> Dict:
    """Generates the email body using Groq."""
    print("Generating email body using Groq...")
    prompt = prompt_template_body.format_messages(
        leetcode_title=state["leetcode_title"],
        leetcode_difficulty=state["leetcode_difficulty"],
    )
    response = model.invoke(prompt)
    body = response.content.strip()
    print(f"Generated email body (first 100 chars): {body[:100]}...")
    return {"email_body": body}


def send_email_func(state: MonitoringState) -> Dict:  # Changed return type
    """Sends an email based on the state."""
    subject = state.get("email_subject", "LeetCode Update")
    body = state.get("email_body", "Check the LeetCode problem.")
    email_sent = send_email(subject, body)  # Capture the boolean result
    # Always return a dict to update the state, include the boolean result
    return {"email_sent": email_sent}


def update_last_email_time(state: MonitoringState) -> Dict:
    """Updates the last email time in the state."""
    return {"last_email_time": datetime.now(tz=datetime.now().astimezone().tzinfo)}


def is_solved(state: MonitoringState) -> bool:
    """Checks if the LeetCode problem status is 'solved'."""
    return state["status"] == "solved"


# --- LangGraph Definition ---
def create_monitoring_graph():
    builder = StateGraph(MonitoringState)

    builder.add_node("fetch_info", fetch_leetcode_data)
    builder.add_node("decide_send_email", decide_send_email)
    builder.add_node("generate_subject", generate_email_subject)
    builder.add_node("generate_body", generate_email_body)
    builder.add_node("send_email", send_email_func)
    builder.add_node("update_time", update_last_email_time)

    builder.set_entry_point("fetch_info")

    builder.add_conditional_edges(
        "fetch_info",
        lambda state: state.get("status") == "error" or not state.get("leetcode_title"),
        {True: END, False: "decide_send_email"},
    )

    builder.add_conditional_edges(
        "decide_send_email",
        lambda state: state["should_send_email"],
        {True: "generate_subject", False: END},
    )

    builder.add_edge("generate_subject", "generate_body")
    builder.add_edge("generate_body", "send_email")
    builder.add_edge("send_email", "update_time")

    builder.add_conditional_edges(
        "update_time",
        is_solved,
        {False: "fetch_info", True: END},
    )

    return builder.compile()


monitoring_graph = create_monitoring_graph()


# --- Workflow Execution ---
def run_monitoring_workflow():
    print(
        f"Running monitoring workflow at {datetime.now(tz=datetime.now().astimezone().tzinfo).strftime('%Y-%m-%d %I:%M %p %Z%z')} (Coimbatore time)"
    )
    initial_state = MonitoringState(
        leetcode_data={},
        leetcode_title="",
        leetcode_difficulty="",
        leetcode_title_slug="",
        status="unknown",
        should_send_email=False,
        email_subject="",
        email_body="",
        last_email_time=None,
    )
    results = monitoring_graph.invoke(initial_state)
    print("Monitoring workflow finished.")


# --- Scheduling ---
if __name__ == "__main__":
    run_monitoring_workflow()
