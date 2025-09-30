from dotenv import load_dotenv
#load_dotenv()

from crewai import LLM, Agent, Task, Crew
import os
from openai import OpenAI
from pathlib import Path
from crewai.tools import BaseTool

global_env_path = Path.home() / ".env"
print(global_env_path)
load_dotenv(global_env_path)
openai_api_key = os.getenv("GLOBAL_OPENAI_API_KEY")

#print(openai_api_key)
# Create the LLM object for use by the agent
llm = LLM(
    model="openai/gpt-4o-mini",
    api_key=openai_api_key
    #temperature=0.1
)

class ReplaceJargonsTool(BaseTool):
    name: str = "Jargon replacement tool"
    description : str = "Replaces jargon with more specific terms. "

    def _run(self, email: str) -> str:
        replacements = {
            "PRX": "Project Phoenix (internal AI revamp project)",
            "TAS": "technical architecture stack",
            "DBX": "client database cluster",
            "SDS": "Smart Data Syncer",
            "SYNCBOT": "internal standup assistant bot",
            "WIP": "in progress",
            "POC": "proof of concept",
            "ping": "reach out"
        }
        suggestions = []
        email_lower = email.lower()
        for jargon, replacement in replacements.items():
            if jargon.lower() in email_lower:
                suggestions.append(f"Consider replacing '{jargon}' with '{replacement}'")

        return "\n".join(suggestions) if suggestions else "No jargon or internal abbreviations detected."

jt = ReplaceJargonsTool()

original_email = """
looping in Priya. TAS and PRX updates are in the deck. ETA for SDS integration is Friday.
Let's sync up tomorrow if SYNCBOT allows 😄. ping me if any blockers.
"""

jt.run(original_email)

#print(original_email)
#print(jt)
# llm = LLM(
#     model="gemini/gemini-2.0-flash",
#     temperature=0.1
# )



email_assistant = Agent(
    role="Email Assistant Agent",
    goal="Improve emails and make them sound professional and clear",
    backstory="A highly experienced communication expert skilled in professional email writing",
    verbose=True,
    tools=[jt],
    llm=llm
)

email_task = Task(
    description=f"""Take the following rough email and rewrite it into a professional and polished version.
    Expand abbreviations:
    '''{original_email}'''""",
    agent=email_assistant,
    expected_output="A professional written email with proper formatting and content.",
)

crew = Crew(
    agents=[email_assistant],
    tasks=[email_task],
    verbose=True
)

result = crew.kickoff()
print(result)


