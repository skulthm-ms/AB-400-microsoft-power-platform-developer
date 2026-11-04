import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, MCPTool

# The agent's name in the Foundry project
AGENT_NAME = "equipment-eligibility-agent"

# The agent already knows the eligibility rule. You don't need to change this.
AGENT_INSTRUCTIONS = """
You are an assistant that answers equipment replacement eligibility questions for an
internal equipment-provisioning system. Employees ask whether they can get a
replacement device.

To answer, look up the employee's record by employee number and the device they're
asking about by asset tag, using the Dataverse tools available to you. Then apply this
rule, in order:

1. If the device's "Damaged beyond repair" value is Yes, the request is eligible.
2. Otherwise, if the device has no "Issued on" date, the request is eligible.
3. Otherwise, if the device was issued on or before 24 calendar months before today's
   UTC date, the request is eligible.
4. Otherwise, the request is not eligible. Tell the employee the date their device
   becomes eligible (the issued-on date plus 24 months), and mention that it would
   also become eligible earlier if it's flagged as damaged beyond repair.

Always name the asset tag and the issued-on date you used in your reasoning, so the
employee can see how you reached the answer.
"""


def create_dataverse_tool() -> MCPTool:
    # Add the Dataverse MCP tool


    return dataverse_tool


def main():
    os.system("cls" if os.name == "nt" else "clear")
    load_dotenv()

    try:
        project_endpoint = os.getenv("PROJECT_ENDPOINT")
        model_deployment = os.getenv("MODEL_DEPLOYMENT")

        # Initialize the project client
        project = AIProjectClient(
            endpoint=project_endpoint,
            credential=DefaultAzureCredential(),
        )
        openai_client = project.get_openai_client()

        # Create (or update) the agent with the Dataverse MCP tool attached
        dataverse_tool = create_dataverse_tool()
        agent = project.agents.create_version(
            agent_name=AGENT_NAME,
            definition=PromptAgentDefinition(
                model=model_deployment,
                instructions=AGENT_INSTRUCTIONS,
                tools=[dataverse_tool],
            ),
        )
        print(f"Agent ready (name: {agent.name}, version: {agent.version})")

        conversation = openai_client.conversations.create()

        while True:
            question = input("\nAsk an equipment eligibility question (or 'quit'): ")
            if question.strip().lower() in ("quit", "exit"):
                break
            if not question.strip():
                continue

            response = openai_client.responses.create(
                conversation=conversation.id,
                input=question,
                extra_body={
                    "agent_reference": {"name": agent.name, "type": "agent_reference"}
                },
            )

            # The first call to a new MCP connection asks the signed-in user to sign in
            # and consent. If that happens, open the link, complete sign-in, then press
            # Enter here to continue the same request.
            consent_links = [
                item
                for item in response.output
                if getattr(item, "type", None) == "oauth_consent_request"
            ]
            if consent_links:
                for item in consent_links:
                    print(f"\nOpen this URL to authorize access: {item.consent_link}")
                input("Press Enter after you complete sign-in and consent...")
                response = openai_client.responses.create(
                    previous_response_id=response.id,
                    input=question,
                    extra_body={
                        "agent_reference": {
                            "name": agent.name,
                            "type": "agent_reference",
                        }
                    },
                )

            print(f"\n{response.output_text}")

    except Exception as ex:
        print(ex)


if __name__ == "__main__":
    main()
