# Challenge 11: Automating Minor Tasks using Copilot Agents

Create and run a GitHub Copilot agent issue that produces up-to-date documentation for the Accessory Service backend API. You will learn to scope the task, hand it off to the agent, and review the generated output.

## Learning Goals

- Describe core Copilot agent capabilities and when to use them.
- Prepare clear, reviewable tasks for an agent.
- Monitor, validate, and iterate on agent-produced documentation.

## Prerequisites

- Access to GitHub Copilot agents in your org.
- Familiarity with the Accessory Service code in `backend/accessory-service/`.
- Ability to create and triage GitHub Issues.

## What To Do

1. **Review the Accessory Service API**: Inspect the FastAPI routes, Pydantic models, and existing docs (if any) to gather required context for accurate documentation.
2. **Assemble Reference Material**: Capture endpoints, request/response schemas, authentication rules, and usage examples the documentation must cover.
3. **Draft the Agent Task**: Turn your findings into a structured GitHub Issue for the Copilot agent, supplying context, acceptance criteria, and output expectations.
4. **Assign and Monitor**: Assign the issue to the agent, observe status updates, and supply clarifications as needed.
5. **Review and Finalize**: Validate the generated documentation against the code, request corrections if gaps remain, and merge the result.

## Success Criteria

- [ ] A Copilot agent receives the documentation task via GitHub Issue.
- [ ] The resulting Accessory Service API docs accurately reflect current routes, payloads, and auth.
- [ ] All agent actions are monitored and reviewed before acceptance.
- [ ] Any follow-up edits are tracked and communicated back through the issue.

## Agent Issue Starting Prompt

Copy the template below into a new GitHub Issue and customize details such as branch names or links:

```markdown
## Task: Generate Accessory Service API Documentation

### Context
- Source code: `backend/accessory-service/main.py`, `models.py`, `config.py`.
- Existing references: check for prior docs in `backend/accessory-service/README.md`.
- Include authentication, error handling, and sample requests.

### Requirements
- Produce Markdown documentation for every public endpoint with method, path, purpose, and request/response schemas.
- Note required headers, auth tokens, and relevant environment variables.
- Provide at least one sample request/response pair per endpoint using curl or HTTP file syntax.
- Cross-reference shared models in other services when used.

### Acceptance Criteria
- [ ] Documentation stored at `docs/accessory-service-api.md` (create file if missing).
- [ ] All endpoints in `main.py` are represented with accurate schemas from `models.py`.
- [ ] Auth and configuration steps validated against `config.py`.
- [ ] Markdown passes linting and renders without warnings.

### Deliverables
- Pull request with the new or updated documentation file.
- Comment summarizing any ambiguities or assumptions.
```

## Note

You may customize the prompt further based on your specific codebase or documentation standards. 
![assign to agent](../../solutions/challenge-11/docs/assign-to-agent.jpg)

And eyou can even create your own agents for recurring  tasks.
![custom agent](../../solutions/challenge-11/docs/github-custom-agent.jpg)

Once the agent completes the issue, review the pull request, suggest fixes if required, and approve when everything matches the service implementation.