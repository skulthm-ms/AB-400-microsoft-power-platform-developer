import asyncio
import sys
import webbrowser
from os import environ

from dotenv import load_dotenv
from msal import PublicClientApplication

from microsoft_agents.activity import ActivityTypes
from microsoft_agents.copilotstudio.client import ConnectionSettings, CopilotClient

load_dotenv()

# Scope used to request a token for the Power Platform API
POWER_PLATFORM_SCOPE = "https://api.powerplatform.com/.default"


def acquire_user_token() -> str:
    """Sign the user in interactively (or reuse a cached token) and return an
    access token for the Power Platform API."""
    app = PublicClientApplication(
        client_id=environ["COPILOTSTUDIOAGENT__AGENTAPPID"],
        authority=f"https://login.microsoftonline.com/{environ['COPILOTSTUDIOAGENT__TENANTID']}",
    )

    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent([POWER_PLATFORM_SCOPE], account=accounts[0])

    if not result:
        print("Opening a browser window to sign in...")
        result = app.acquire_token_interactive(scopes=[POWER_PLATFORM_SCOPE])

    if "access_token" not in result:
        raise RuntimeError(result.get("error_description", "Sign-in failed."))

    return result["access_token"]


def create_client() -> CopilotClient:
    settings = ConnectionSettings(
        environment_id=environ["COPILOTSTUDIOAGENT__ENVIRONMENTID"],
        agent_identifier=environ["COPILOTSTUDIOAGENT__SCHEMANAME"],
        cloud=None,
        copilot_agent_type=None,
        custom_power_platform_cloud=None,
    )
    token = acquire_user_token()
    return CopilotClient(settings, token)


async def chat_loop(client: CopilotClient, conversation_id: str):
    while True:
        query = input("\n>>> ").strip()
        if query.lower() in ("quit", "exit"):
            print("Goodbye!")
            return

        async for activity in client.ask_question(query, conversation_id):
            if activity.type == ActivityTypes.message:
                print(f"\n{activity.text}")
            elif activity.type == ActivityTypes.end_of_conversation:
                print("\nThe agent ended the conversation.")
                return


async def main():
    client = create_client()

    print("Connecting to the equipment questions agent...\n")
    conversation = None
    async for activity in client.start_conversation(True):
        if activity.text:
            print(activity.text)
        conversation = activity.conversation

    await chat_loop(client, conversation.id)


if __name__ == "__main__":
    asyncio.run(main())
