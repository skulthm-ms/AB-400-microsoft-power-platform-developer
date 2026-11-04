---
lab:
    title: 'Integrate a Foundry agent with Power Platform data'
    description: 'Connect a Microsoft Foundry agent to Dataverse through the Model Context Protocol, and consume a Copilot Studio agent through the Copilot Studio client in the Microsoft 365 Agents SDK.'
    level: 400
    duration: 45
    islab: true
    status: 'in-development'
    targetDate: '2026-10-16'
---

# Integrate a Foundry agent with Power Platform data

> **Important**: This is an incomplete testing draft, not a released exercise. The Python starter files are included, but `EquipmentQuestionsAgent.zip` and `EquipmentQuestionsAgent-sample-conversation.md` have not been built. The Copilot Studio import and client-runtime sections are blocked until those assets are supplied. Foundry connection settings, permissions, SDK behavior, and licensing statements below still require verification. Don't treat expected output or fallback descriptions as test evidence. Download the files from the testing branch, not official main.

Neither agent in this exercise is built from scratch. A complete Microsoft Foundry agent project and a complete Copilot Studio agent are both supplied, and your job is to connect them to live data through two different, supported paths: a Foundry agent that reads Dataverse data through the Model Context Protocol (MCP), and a console client that reaches a Copilot Studio agent through the Copilot Studio client in the Microsoft 365 Agents SDK. As a Power Platform developer, the skill this exercise teaches isn't building an agent — it's deciding which agent reaches which data, over which path, and as whom.

You'll wire a Dataverse MCP connection into the supplied Foundry agent, ask it a question that only live data can answer correctly, and then do the same thing again through a completely different mechanism: a Copilot Studio agent reached from a small Python console app.

This exercise should take approximately **45** minutes to complete.

> **Note**: Some of the technologies used in this exercise, including Microsoft Foundry's Model Context Protocol tool and the Microsoft 365 Agents SDK Copilot Studio client, are in active development. You may experience some differences from what's described here, including changed menu labels or dialog layouts.

## Prerequisites

To complete this exercise, you need:

- Access to the Power Platform developer environment used in the other exercises in this course, with the base Dataverse solution installed (see `00-setup`).
- An [Azure subscription](https://azure.microsoft.com/free/){:target="_blank"} with permission to create a resource group and a Microsoft Foundry project with a model deployment.
- Rights to register applications in Microsoft Entra ID for your tenant (or an administrator who can do this for you — see the note in the relevant task if self-service app registration is turned off).
- A [Microsoft Copilot Studio](https://copilotstudio.microsoft.com){:target="_blank"} license that can publish agents. A trial license can't publish — see the note in the relevant task for an alternative if this applies to you.
- [Visual Studio Code](https://code.visualstudio.com/){:target="_blank"} with the Python extension.
- [Python 3.12](https://www.python.org/downloads/){:target="_blank"} or later.
- [Git](https://git-scm.com/downloads){:target="_blank"}.

> **Note**: The draft targets Python 3.12; a complete live walkthrough has not yet been verified.

## Confirm the base solution and reset the lab data

Every exercise in this course shares the same Dataverse tables and seed data, so you start here the same way you'd start any of the others.

1. Sign in to [Power Apps](https://make.powerapps.com){:target="_blank"} at `https://make.powerapps.com`, and select the developer environment you've been using for this course.
1. Select **Solutions**, and confirm that **Equipment Provisioning (base)** is listed. If it isn't, follow the import steps in [`00-setup`](./00-setup.md) before you continue.
1. Open the **Equipment Provisioning** app, go to the **Employees** or **Requests** view, and select **Reset lab data** on the command bar.
1. Wait for the confirmation dialog, then select **Refresh**.

    You should see a summary such as "Reset 5 employees, 9 devices, 6 requests and 4 allowances... EMP-001 is linked to you." This links the employee record `EMP-001` (Avery Chen) to your own sign-in, which matters later: when you ask the agent "Am I eligible for a replacement laptop?", it answers for you.

## Enable the Dataverse MCP server

Microsoft Dataverse can act as an MCP server, so an MCP-compatible client like a Foundry agent can query it. The server is already enabled for Copilot Studio by default, but you need to turn it on more generally before another kind of client can connect.

1. Open the [Power Platform admin center](https://admin.powerplatform.microsoft.com){:target="_blank"} at `https://admin.powerplatform.microsoft.com`, and select **Environments**.
1. Select your developer environment, then select **Settings**.
1. Under **Settings**, select **Product** > **Features**, and scroll down to **Dataverse Model Context Protocol**.
1. Confirm that **Allow MCP clients to interact with Dataverse MCP server** is turned on. Turn it on if it isn't.

    > **Note**: This setting is environment-level and reversible, so turning it on doesn't affect any other exercise.

1. Go back to [Power Apps](https://make.powerapps.com){:target="_blank"}, select the gear icon, and select **Session details**.
1. Note the **Instance URL** shown there (for example, `https://org1234abcd.crm.dynamics.com/`). You'll use this twice in the next task: as the Dataverse MCP server address, and when you register the client that's allowed to call it.

## Connect the supplied Foundry agent project to the Dataverse MCP server

Now you'll create a Foundry project, deploy a model, and wire the supplied agent project to the Dataverse MCP server. The agent's instructions already contain the eligibility rule — you're not writing or editing any of the agent's reasoning, only adding the connection it uses to read data.

### Create a Foundry project and deploy a model

1. Open Visual Studio Code.
1. Select **Extensions** (**Ctrl+Shift+X**) and search for `AI Toolkit`. Install the **AI Toolkit** extension if it isn't already installed.
1. In the Extensions list, expand **AI Toolkit** and select **Resources**.
1. Select **Sign in to Azure...** and follow the process to sign in to your Azure account.
1. In the AI Toolkit Resources list, select **+ Create Project**.
1. Create a project with the following settings:
    - **Project name**: *A unique name, for example `ab400-lab10-foundry`*
    - **Azure subscription**: *Your Azure subscription*
    - **Resource group**: *Create a new resource group or select an existing one*
    - **Region**: *Any available region*
1. Select **Create Project**, and wait for the project to finish provisioning.
1. In the **Model Catalog**, search for and select `gpt-4.1`, then select **Deploy**. Accept the default deployment settings and wait for the deployment to finish.
1. Expand the project in **Resources**, expand **Project Endpoints**, and select **Copy Project Endpoint**. Paste it somewhere you can retrieve it in a moment (for example, a scratch file in Visual Studio Code).

    You should now have a Foundry project with one deployed model, and its endpoint copied to hand.

### Register an Entra app for the Dataverse connection

The Foundry agent's connection to the Dataverse MCP server is authenticated with Microsoft Entra ID, using your own sign-in — the same way you already sign in to Power Apps and Foundry. To make that possible, Dataverse needs to recognize the application that's asking.

1. Open the [Microsoft Entra admin center](https://entra.microsoft.com){:target="_blank"} at `https://entra.microsoft.com`.
1. Select **Identity** > **Applications** > **App registrations**, and then select **New registration**, or select an existing registration named `ab400-lab10-mcp` if you've already created one.
1. If you're creating a new registration, use these settings:
    - **Name**: `ab400-lab10-mcp`
    - **Supported account types**: Accounts in this organizational directory only
    - **Redirect URI**: Select **Public client/native (mobile & desktop)**, and enter `http://localhost`
1. Select **Register**.
1. On the **Overview** page, note the **Application (client) ID** and the **Directory (tenant) ID**. You'll need both shortly.
1. Select **API permissions** > **Add a permission** > **APIs my organization uses**, and search for `Dynamics CRM`.
1. Select the **Delegated permissions** list, select `mcp.tools`, and then select **Add permissions**.

    > **Note**: If you don't see **Dynamics CRM** in the list, the Power Platform API hasn't been used in your tenant yet. Ask a tenant administrator to grant consent once using the steps in [Power Platform API authentication](https://learn.microsoft.com/power-platform/admin/programmability-authentication-v2){:target="_blank"} at `https://learn.microsoft.com/power-platform/admin/programmability-authentication-v2`, or use the restricted-exercise alternative in the Learn unit.

1. Back in the Power Platform admin center, return to your environment's **Dataverse Model Context Protocol** settings (the page you used in the previous task), and select **Advanced Settings**.
1. Select **+ New client** (or similar), and add a new entry:
    - **Name**: `ab400-lab10-mcp`
    - **Application (client) ID**: *the client ID you noted above*
1. Set **Is Enabled** to **Yes**, and select **Save & Close**.

    > **Important**: If your tenant blocks self-service app registration, or blocks user consent to API permissions, ask an administrator to complete this task, or use the restricted-exercise alternative described in the Learn unit, which inspects a recorded trace of the agent's MCP tool call instead of running it live.

### Add the Dataverse MCP server as a tool and run the agent

1. In the [Foundry portal](https://ai.azure.com){:target="_blank"} at `https://ai.azure.com`, open your project.
1. Select **Manage**, select **Project details**, and select the **Connected resources** tab.
1. Select **New connection**, then select **Custom**, and then select **MCP**.
1. Configure the connection:
    - **Name**: `ab400-lab10-dataverse-mcp`
    - **Server URL**: *your Dataverse instance URL, with `api/mcp` appended, for example `https://org1234abcd.crm.dynamics.com/api/mcp`*
    - **Authentication**: OAuth Identity Passthrough
    - **Client ID**: *the Application (client) ID of `ab400-lab10-mcp`*
    - **Client secret**: *leave blank — this app has none*
    - **Auth URL**: `https://login.microsoftonline.com/{tenantId}/oauth2/v2.0/authorize` (substitute your tenant ID)
    - **Token URL** and **Refresh URL**: `https://login.microsoftonline.com/{tenantId}/oauth2/v2.0/token`
    - **Scopes**: the scope shown for the `mcp.tools` permission on your app registration's **API permissions** page, followed by a space and `offline_access`
1. Select **Create**.
1. In Visual Studio Code, open the `Allfiles/10-foundry-agent-integration/foundry-agent` folder from the lab files you cloned in the setup. If you didn't clone the repository, download the files directly:
    - [agent.py](https://raw.githubusercontent.com/skulthm-ms/AB-400-microsoft-power-platform-developer/test-lab10-integration/Allfiles/10-foundry-agent-integration/foundry-agent/agent.py){:target="_blank"} from `https://raw.githubusercontent.com/skulthm-ms/AB-400-microsoft-power-platform-developer/test-lab10-integration/Allfiles/10-foundry-agent-integration/foundry-agent/agent.py`
    - [requirements.txt](https://raw.githubusercontent.com/skulthm-ms/AB-400-microsoft-power-platform-developer/test-lab10-integration/Allfiles/10-foundry-agent-integration/foundry-agent/requirements.txt){:target="_blank"} from `https://raw.githubusercontent.com/skulthm-ms/AB-400-microsoft-power-platform-developer/test-lab10-integration/Allfiles/10-foundry-agent-integration/foundry-agent/requirements.txt`
    - [.env](https://raw.githubusercontent.com/skulthm-ms/AB-400-microsoft-power-platform-developer/test-lab10-integration/Allfiles/10-foundry-agent-integration/foundry-agent/.env){:target="_blank"} from `https://raw.githubusercontent.com/skulthm-ms/AB-400-microsoft-power-platform-developer/test-lab10-integration/Allfiles/10-foundry-agent-integration/foundry-agent/.env`
1. In the **Command Palette** (**Ctrl+Shift+P**), use the command `Python: Select Interpreter`, and create a new **Venv** environment based on Python 3.12.
1. Right-click the **foundry-agent** folder and select **Open in integrated terminal**. Confirm the prompt shows **(.venv)**.
1. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

1. Open the **.env** file, and update the values:
    - `PROJECT_ENDPOINT`: the project endpoint you copied earlier
    - `MODEL_DEPLOYMENT`: the name of the model you deployed (for example, `gpt-4.1`)
    - `DATAVERSE_MCP_URL`: your Dataverse instance URL with `api/mcp` appended
    - `MCP_CONNECTION_NAME`: `ab400-lab10-dataverse-mcp`

    Save the file (**Ctrl+S**).
1. Sign in to Azure from the terminal, so `DefaultAzureCredential` can authenticate the Foundry project client:

    ```bash
    az login
    ```

1. Open **agent.py**, and find the comment **Add the Dataverse MCP tool**. Add the following code above the `return` statement:

    ```python
    # Add the Dataverse MCP tool
    dataverse_tool = MCPTool(
        server_label="dataverse",
        server_url=os.getenv("DATAVERSE_MCP_URL"),
        allowed_tools=["read_query", "search_data", "search", "describe"],
        require_approval="never",
        project_connection_id=os.getenv("MCP_CONNECTION_NAME"),
    )
    ```

    This is the only code you write in this exercise. The `allowed_tools` list restricts the connection to read-only operations — the agent can never create, update, or delete a Dataverse row through this tool, no matter what it's asked.

1. Save the file, and run the agent:

    ```bash
    python agent.py
    ```

1. Complete the one-time sign-in that the first request triggers: if a consent link is printed, open it in a browser, sign in with the same account you used earlier, and approve access. Then return to the terminal and press **Enter** to continue.

You should see "Agent ready" printed, followed by a prompt asking for a question. Leave the agent running — you'll ask it a question in the next task.

> **Tip**: If the request fails because a rate limit is exceeded, wait a few seconds and try again.

## Ask the agent a grounded equipment question

This is the first half of the exercise's ta-da moment: you'll see the agent answer correctly using data it just read, not anything hard-coded.

1. At the agent's prompt, ask:

    ```input
    Am I eligible for a replacement laptop?
    ```

1. Review the agent's response.

    ```output
    Based on your record (EMP-001), your laptop LAP-1001 was issued approximately 8 months ago
    and isn't flagged as damaged beyond repair. Devices become eligible for replacement 24 months
    after they're issued, so LAP-1001 isn't eligible yet. It will become eligible around [issued
    date + 24 months], or sooner if it's later flagged as damaged beyond repair.
    ```

    The exact wording varies, but the answer should be **not eligible**, and it should name `LAP-1001` and its issue date — the same reasoning as the rule you've seen enforced elsewhere in this course, now applied by an AI agent reading Dataverse live through MCP rather than calling a stored procedure.

1. In the [Foundry portal](https://ai.azure.com){:target="_blank"}, open your project, select your agent, and open its most recent run (or thread) in the testing pane. Find the tool call to the `dataverse` MCP server, and review the arguments and the data it returned.

    You should see a `read_query` or `search_data` call naming the `eqp_employee` and `eqp_device` tables — proof the answer came from a live query, not from the agent's instructions.

1. Ask a second question for a device that's well past its replacement window, to see the eligible path too:

    ```input
    What about my phone?
    ```

    ```output
    Your phone PHN-1002 was issued about 26 months ago and isn't damaged. Since more than 24
    months have passed, you're eligible for a replacement.
    ```

Great — you've connected a Foundry agent to live Power Platform data through MCP, and watched it reason over real rows instead of a canned answer.

## Compare results with a second identity (optional)

If you have access to a second user in the same environment, you can see the same agent give a different, still-correct answer without changing a single line of its instructions — because the Dataverse MCP server enforces ordinary Dataverse security roles, not something the agent decides.

1. If a second user is available, sign in to Power Apps as that user and run **Reset lab data** so their identity is linked to an employee record (for example, `EMP-005`, which holds the **Equipment Requester** role rather than **Equipment Coordinator**).
1. Ask that second user to run `python agent.py` from their own machine (or their own signed-in session), and ask the same question. The first run prompts them to sign in and consent, just as it did for you. Compare their answer and, if applicable, any access difference you observe.

If a second user isn't available — developer environments are intended for a single owner, so this often isn't possible — open the **Equipment Requester** and **Equipment Coordinator** role definitions in the Power Platform admin center instead (**Environments** > your environment > **Settings** > **Users + permissions** > **Security roles**). **Equipment Requester** has user-level read, create, and write on Request, with organization-level read on Employee, Device, and Allowance. **Equipment Coordinator** adds organization-level write. Explain which privilege difference would change the Foundry agent's answer, and which wouldn't, given that its MCP tool is read-only regardless of role.

## Publish the supplied Copilot Studio agent

The second half of this exercise proves there's more than one supported way to reach the same kind of data: a Copilot Studio agent, reached from a plain console client rather than the Foundry agent's MCP tool.

> **Important**: Stop this path here. The required agent solution ZIP and recorded test conversation are absent from this snapshot. Building and exporting the real solution is prerequisite authoring work, not an instruction for the learner to build an agent from scratch. Verify the supported solution export/import process before supplying the package. Don't fabricate a ZIP or transcript.

1. After the genuine `EquipmentQuestionsAgent.zip` has been supplied and verified, download it from the supplied artifact location. No package download is available in this snapshot.
1. Open [Copilot Studio](https://copilotstudio.microsoft.com){:target="_blank"} at `https://copilotstudio.microsoft.com`, and select your environment.
1. Open the solution explorer, select **Import solution**, browse to the file you downloaded, and complete the import.
1. In the imported solution, open the **Equipment Questions Agent**, or select it if it's already been imported and published in this environment.
1. Select **Publish**.

    > **Important**: Publishing requires a Microsoft 365 Copilot license, a Copilot Studio User License, or (for agents with no generative-AI features) an Office license. A Copilot Studio **trial** license can't publish an agent. If you only have a trial license, skip publishing: instead, open the agent's topics and a recorded test conversation (included with the download), and explain what publishing would unlock — the same inspect-and-explain pattern used elsewhere in this course when a feature needs a license you may not have.
    <!-- The recorded conversation is also a missing prerequisite, not supplied fallback evidence. -->

1. Once published, select **Settings** > **Advanced** > **Metadata**, and note the **Environment ID** and **Schema name**. You'll need both in the next task.

## Register an app for the Copilot Studio client

The Copilot Studio client in the Microsoft 365 Agents SDK needs an application identity to sign in with, the same way any native app does.

1. Open the [Microsoft Entra admin center](https://entra.microsoft.com){:target="_blank"} at `https://entra.microsoft.com`.
1. Select **Identity** > **Applications** > **App registrations**, and select **New registration**, or select an existing registration named `ab400-lab10-client` if you've already created one.
1. If you're creating a new registration, use these settings:
    - **Name**: `ab400-lab10-client`
    - **Supported account types**: Accounts in this organizational directory only
    - **Redirect URI**: Select **Public client/native (mobile & desktop)**, and enter `http://localhost`
1. Select **Register**.
1. On the **Overview** page, note the **Application (client) ID** and the **Directory (tenant) ID**.
1. Select **API permissions** > **Add a permission** > **APIs my organization uses**, and search for `Power Platform API`.
1. Select the **Delegated permissions** list, select `CopilotStudio.Copilots.Invoke`, and select **Add permissions**.
1. Select **Add a permission** again, select **Microsoft Graph**, select the **Delegated permissions** list, select `User.Read`, and select **Add permissions**.

    > **Note**: This app registration is a public client with no secret — interactive sign-in is all it needs. If your tenant blocks self-service app registration or blocks user consent to these permissions, ask an administrator to complete this task, or use the restricted-exercise alternative in the Learn unit, which reviews a recorded transcript of the client's request and response instead of running it live.

## Configure and run the Copilot Studio client

This is the second half of the ta-da moment: the same kind of equipment question, answered through a completely different, independently authenticated path.

1. In Visual Studio Code, open the `Allfiles/10-foundry-agent-integration/copilot-studio-client` folder from the lab files you cloned in the setup, or download the files directly:
    - [client.py](https://raw.githubusercontent.com/skulthm-ms/AB-400-microsoft-power-platform-developer/test-lab10-integration/Allfiles/10-foundry-agent-integration/copilot-studio-client/client.py){:target="_blank"} from `https://raw.githubusercontent.com/skulthm-ms/AB-400-microsoft-power-platform-developer/test-lab10-integration/Allfiles/10-foundry-agent-integration/copilot-studio-client/client.py`
    - [requirements.txt](https://raw.githubusercontent.com/skulthm-ms/AB-400-microsoft-power-platform-developer/test-lab10-integration/Allfiles/10-foundry-agent-integration/copilot-studio-client/requirements.txt){:target="_blank"} from `https://raw.githubusercontent.com/skulthm-ms/AB-400-microsoft-power-platform-developer/test-lab10-integration/Allfiles/10-foundry-agent-integration/copilot-studio-client/requirements.txt`
    - [.env](https://raw.githubusercontent.com/skulthm-ms/AB-400-microsoft-power-platform-developer/test-lab10-integration/Allfiles/10-foundry-agent-integration/copilot-studio-client/.env){:target="_blank"} from `https://raw.githubusercontent.com/skulthm-ms/AB-400-microsoft-power-platform-developer/test-lab10-integration/Allfiles/10-foundry-agent-integration/copilot-studio-client/.env`

    > **Tip**: The code used in this exercise is based on the Copilot Studio client in the Microsoft 365 Agents SDK for Python. The same client library is also available for .NET and JavaScript. See [Integrate with Copilot Studio](https://learn.microsoft.com/microsoft-365/agents-sdk/integrate-with-mcs){:target="_blank"} at `https://learn.microsoft.com/microsoft-365/agents-sdk/integrate-with-mcs` for details.

1. In the **Command Palette** (**Ctrl+Shift+P**), use the command `Python: Select Interpreter`, and create a new **Venv** environment based on Python 3.12.
1. Right-click the **copilot-studio-client** folder and select **Open in integrated terminal**. Confirm the prompt shows **(.venv)**.
1. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

1. Open the **.env** file and update the values:
    - `COPILOTSTUDIOAGENT__ENVIRONMENTID`: the Environment ID you noted from the agent's metadata
    - `COPILOTSTUDIOAGENT__SCHEMANAME`: the Schema name you noted from the agent's metadata
    - `COPILOTSTUDIOAGENT__TENANTID`: the Directory (tenant) ID from the `ab400-lab10-client` app registration
    - `COPILOTSTUDIOAGENT__AGENTAPPID`: the Application (client) ID from the `ab400-lab10-client` app registration

    Save the file (**Ctrl+S**).
1. Run the client:

    ```bash
    python client.py
    ```

1. Sign in using your own credentials in the browser window that opens, and complete any consent prompt.
1. Once connected, ask a similar question:

    ```input
    Can I get a replacement laptop?
    ```

1. Review the agent's response. It should answer the question, through the Copilot Studio agent's own Dataverse integration — a different path than the Foundry agent's MCP tool, and reached under your own delegated user identity rather than the code app connector pattern used elsewhere in this course.
1. When you've finished testing, close the client with **Ctrl+C**, and deactivate the Python environment:

    ```bash
    deactivate
    ```

> **Tip**: If the request fails because a rate limit is exceeded, wait a few seconds and try again.

You've now reached the same kind of equipment data through two independent, supported paths: a Foundry agent grounded through the Dataverse MCP server, and a Copilot Studio agent reached through the Copilot Studio client in the Microsoft 365 Agents SDK — each under a different identity, proving there's more than one supported way for Foundry and Copilot Studio agents to work together. The developer's job is choosing which path reaches which data, over which identity.

## Clean up

If you've finished exploring the services used in this exercise, delete the resources you created to avoid incurring unnecessary Azure costs.

1. Review the resources created during testing in the [Azure portal](https://portal.azure.com){:target="_blank"} at `https://portal.azure.com`. Delete a resource group only if you created it exclusively for this test and it contains no unrelated resources. In an existing or shared group, delete only verified test-owned resources; preserve the group and its original contents.

Record the original Dataverse MCP/client settings and restore only the settings changed for this test. Inventory any test-created app registrations or agents and remove them only after checking ownership and dependencies. Don't delete reused resources or change unrelated identities. No published Copilot Studio agent should be assumed to exist merely because its instructions appear in this draft.

## Summary

In this exercise, you added the Dataverse MCP server as a tool to a supplied Microsoft Foundry agent, using an Entra-based connection, and watched it answer an equipment eligibility question by reading live Dataverse data instead of relying on a hard-coded response. You then registered an app and ran a supplied Python console client built on the Copilot Studio client in the Microsoft 365 Agents SDK to reach a published Copilot Studio agent through a second, independent path. Neither agent was built in this exercise — the skill you practiced was integration: deciding which agent reaches which data, over which path, and as whom.

You have successfully completed this exercise.
