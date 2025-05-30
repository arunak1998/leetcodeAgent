
📩 Daily LeetCode Email Automation Agent
========================================

This project automates fetching the daily LeetCode question and sends a well-formatted email every 2 hours (if unsolved). It uses LangGraph + Groq + SMTP to create a clean agentic pipeline.

🔧 Features
-----------
- ✅ Fetches daily LeetCode problem from the API.
- 📬 Generates a professional, structured email using **Groq's LLaMA-3-70B model**.
- 🧠 Uses **LangGraph** to orchestrate each step like an agent workflow.
- ⏰ Emails are sent every 2 hours unless marked "solved".
- 🔒 Keeps track of the last sent timestamp to prevent spamming.
- 📨 Sends email using secure SMTP with Gmail (or any provider).

📂 Project Structure
--------------------
.
├── agents.py                 # Main agent script (this file)
├── src/
│   └── utils/
│       └── leetcode.py       # Custom function to get daily question via API
├── .env                      # Secret credentials
└── requirements.txt          # Python dependencies

🛠️ How It Works
----------------
1. `fetch_info`  
   Fetches the daily LeetCode question via your own API wrapper.

2. `decide_send_email`  
   Checks if:
   - The question is not marked solved
   - 2+ hours have passed since the last email

3. `generate_subject`  
   Creates an email subject like:  
   > LeetCode: Two Sum (Easy)

4. `generate_body`  
   Uses `ChatGroq` to craft a friendly yet technical email body with problem details.

5. `send_email`  
   Uses Gmail SMTP to send the email.

6. `update_time`  
   Marks the current time as the last email sent timestamp.

⚙️ Setup Instructions
---------------------
1. Clone This Repo
```bash
git clone https://github.com/your_username/daily-leetcode-agent.git
cd daily-leetcode-agent
