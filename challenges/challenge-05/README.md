# Challenge 05: GitHub Copilot – From Enabled to Effective

## Overview
So far we have used GitHub Copilot to brainstorm ideas, analyze business context, create Issues and iterativelly work on Product Requirements Document. In fact we have used few tools such as GitHub MCP Server. Now it is time to expand on this and see how will GitHub Copilot help us with all remaining challenges.

## Copilot basics

### Model selection
- Auto - let Copilot decide what model to use, if it selects premium model than 1x gets discounted to 0.9x
- Base models do not consume premium requests (0x)
  - Use it for simple text tasks and searches. 
  - As of October 2025 I prefer GPT-5-mini
- Premium models consume premium requests, most often one per request (1x)
  - 10x models if available work just slightly better and are order of magnitude more expensive and slow, typically you will not prefer those
  - Switch model when Copilot is not able to move beyond some issue or after previous one finished so you get second opinion
  - As of November 2025 we would usually combine GPT-5.1-Codex and Claude Sonnet 4.5 for coding and GPT-5.1 or Gemini 2.5 Pro for document writing and brainstorming
  - 0.33x models are faster and save few requests, but quality is lower (we would usually use 1x model for everything except for simple tasks with GPT-5-mini)  

### Codebase Search
Ask Copilot to search and understand your code. Copilot will automatically use search tools, but if you want to be very explicit, you can reference tool with `#`, for example `#codebase` to explicitly search codebase. You also use this symbol to put specific file into context - either using mouse or `#myfile.py`.

```markdown
How are collections in database created in our project? Point me to specific libraries and sections of code.
```

Experiment with different models selection and see their different outputs and approaches.

### Generating documentation
Create new file MY_NEW_DOCS.md, add it to context (drag and drop or using `#`) and let's iterativelly ask for documentation. After each step, if you are satisfied, click Keep so you can track differences.

- `Look at challenged folder and create list of challanges with two senteces per each, capture main topic. Use differen Unicode emoji for each.`
- `Look at my backend folder and check for environmental variables we are using for configuration. Create Markdown table with list with simple description and add it to #MY_NEW_DOCS.md.`
- `Services in our backend use Pydantic models to define various data schemas. I want to draw data model of our application using mermaid, add those to #MY_NEW_DOCS.md.`

You can use Markdown preview (CTRL+SHIFT+P and search for it) to see diagram rendered.

## Web Search and Fetch

Ask questions about current information:

Try without tools using just model knowledge.
```
When did Microsoft released Microsoft Agent Framework SDK for Python and what is current version? Do NOT use any tools.
```

If you have specific documentation in mind, you can just reference it here (eg. llms.txt or llms-full.txt, see)

```
When did Microsoft released Microsoft Agent Framework SDK for Python and what is current version?
#fetch 
https://github.com/microsoft/agent-framework/releases
https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview

#githubRepo microsoft/agent-framework
```

You can also add web search tools such as `Tavily`.

## Agent Mode
Agent mode provides iterative session where agent works on task by researching, reasoning, coding, using tools and eve (with your permissions) running tests, deployments, compilations and so on.

Let's try something complex to see how agent iterates, makes mistakes and figuring out how to move forward.

```markdown
Create new backend service called discussions-service that provides API and backend for discussions between pet owners.

# Solution Architecture
- Python with FastAPI framework
- CosmosDB as backend database (NoSQL document store)
- Discussion rooms (public and private) with invitation system
- Message threads with support for text and attachments
- Room membership management and access control
- No authentication required at this point (simplified for demo)
- Comprehensive unit tests for all API endpoints
- Integration tests covering full workflows (create room, invite users, post messages, attach files, delete)

# Implementation steps
- Create base folder in backend/discussions-service and initialize with uv
- Design Pydantic models for rooms, messages, invitations, and attachments
- Implement mocked CRUD APIs for rooms, messages, invitations, and attachments
- Write and run unit tests for all mocked endpoints
- Use Azure CLI to provision CosmosDB account with appropriate database and containers
- Store CosmosDB connection details and credentials in .env file
- Add database connection code and write integration tests to verify CosmosDB accessibility
- Implement automatic schema/container creation for rooms, messages, invitations, and attachments collections
- Replace mocked implementations with real CosmosDB operations using cosmos SDK
- Write and execute comprehensive integration test suite covering: create public/private rooms, invite users, post messages with attachments, query discussions, delete operations
- Create detailed README.md documenting architecture, data models, API endpoints, and usage examples
```

As you can see agent can be very powerful, but requires very specific guadance, rules and tools. We will use agent to implement our `accessory` service later, but before we do so, we need to create coding guidelines, add tools and in nech challenge author comprehensive technical specification.

## Customize Copilot to fit our project needs
There are instructions we want our agents to read for every single request to define desired behavior, most important coding standards, project organization, documentation strategy and so on. This live in standardized [AGENTS.md](https://agents.md/) file. We have [AGENTS.md template](https://github.com/CZSK-MicroHacks/MicroHack-GitHub-engineering-constitution/blob/main/templates/AGENTS.md) for our MicroHack organization that we will derive `AGENTS.md` for our repo by combining template, guidelines for specific languages and technical stack we are using and other specifics for this repo.

Use GitHub Copilot to draft `AGENTS.md` for us using following prompt:

```markdown
You task is to create AGETNS.md with robust instructions based on #fetch https://agents.md/
- Use our `AGENTS.md` template from https://raw.githubusercontent.com/CZSK-MicroHacks/MicroHack-GitHub-engineering-constitution/refs/heads/main/templates/AGENTS.md
- In our project we use Python, you can see extended coding standards here: https://raw.githubusercontent.com/CZSK-MicroHacks/MicroHack-GitHub-engineering-constitution/refs/heads/main/standards/python.md
- For Infrastructure as Code we use Bicep, see extended standards here: https://raw.githubusercontent.com/CZSK-MicroHacks/MicroHack-GitHub-engineering-constitution/refs/heads/main/standards/bicep.md
- This project is targeting simplicity to facilitate learning, emphasize that in `AGENTS.md` - do not overcomplicate, do not do premature abstractions and so on
```

See resulting `AGENTS.md` file and you can make modifications to fit your needs.

There might be complex prompts you use often or you want to share with other developers in your repository. For that we can use Prompt Files. Create file `.github/prompts/headerComments.prompt.md` with this content:

````markdown
---
description: Add Python class and function header comments in a specific visual style
argument-hint: Specify style (HashBlock, AsciiBox...) and target (active file, folder...)
agent: agent
tools: []
---
Make sure user provided style in ${input:style} and target in ${input:target}. If not, do not continue and ask for them again.

The `target` input specifies the scope of the operation. It can be:
- "active file" or "current file"
- A specific file path
- A directory path (to apply to all files in that directory)
- A glob pattern (e.g., "**/*.py")

Based on the style provided, add visual function header comments before each function definition or class in the Python files specified by `target`. 
If there are already header comments present, replace them with the new style.

Use the following definitions for the styles:

1. **HashBlock**:
   ```python
   ###############################################################################
   # FUNCTION NAME
   ###############################################################################
   ```

2. **AsciiBox**:
   ```python
   # +-----------------------------------------------------------------------------+
   # |                                FUNCTION NAME                                |
   # +-----------------------------------------------------------------------------+
   ```

3. **ArrowSeparator**:
   ```python
   # -----------------------------> FUNCTION NAME <-----------------------------
   ```

4. **DoubleDashBlock**:
   ```python
   # =============================================================================
   # FUNCTION NAME
   # =============================================================================
   ```

5. **StarBanner**:
   ```python
   # ****************************** FUNCTION NAME ******************************
   ```

6. **Minimal**:
   ```python
   # --- FUNCTION NAME ---
   ```

Apply the selected style to all Python functions and classes in the files matching the `target`.
````

Try it now with prompt `/headerComments DoubleDashBlock in activity service`

There is more you can customize in Copilot, but this is enough for our need.

## Adding MCP tools
So far we have used many built-in tools so Copilot can edit files, merge, search repository and also leverage MCP tool #fetch that allow downloading sources from Internet. There are much more advanced MCP Servers available. Click on tools ico next to model selection and see what is installed in your environment. Click on MCP icon next to Configure tools and `Browse MCP Servers` to see some from GitHub catalog. Find `Microsoft Learn` and install it.

Try new MCP server with `I need official code example on how to use Azure SDK in Python to use managed identity to authenticate to Azure SQL` which will likely make Copilot select out new tool ans search in documentation (or you can force it with #Microsoft Docs).

You can bring any MCP Server you want by default, but Copilot enterprise administrators can also create curated list of solutions. Look at one of [MCP catalogs](https://mcpserverdirectory.org/) where you will find tools for accessing Azure, GitHub, SQL, PostgreSQL, Kubernetes, Jira, ServiceNow and many more. Very useful is Playwright MCP (by Microsoft, you will find in official GitHub MCP catalog) so you can automate UI testing, but this is currently not supported in Codespaces (requires browser). Another good example is Figma MCP so you can integrate with screen designs.

We can install for example Git MCP outside of built-in catalog - click on tools, MCP icon and MCP server command `uvx mcp-server-git`. Test it with prompt `What changed in last 3 commits?`

## Success criteria

- [ ] Used Copilot to search codebase and generate documentation in `MY_NEW_DOCS.md`
- [ ] Used `#fetch` to retrieve external documentation into context
- [ ] Experimented with Agent Mode to scaffold a complex feature
- [ ] Created `AGENTS.md` to customize Copilot behavior for the project
- [ ] Created and tested a custom prompt file `.github/prompts/headerComments.prompt.md`
- [ ] Installed and used an MCP server (e.g. Microsoft Learn or Git) 

**Don't open until after you finish the challenge iterations**
<details>

<summary>Help / Solution</summary>

View solution here: [Challenge 05 Solution](../../solutions/challenge-05/README.md)

</details>

## Next Step
Proceed to next challenge: [Challenge 06](../challenge-06/README.md)
