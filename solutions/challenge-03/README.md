# Solution: Challenge 03

This solution will be provided during the workshop or can be developed as part of the learning exercise.

## Overview

Detailed solution steps and implementation guidance will be available here.

## Key Learning Points

- Implementation strategies and best practices
- Common pitfalls and how to avoid them  
- Success validation criteria
- Next steps and additional resources

## Solution Approach

Solution via `devcontainer.json` configuration and setup scripts.

> note: We haven't discussed the `forwardPorts`, `portsAttributes` properties in the workshop yet (comming later), but it is included here for completeness.

```json
{
	"name": "MicroHack-GitHub",
	"image": "mcr.microsoft.com/devcontainers/universal:2",
	"workspaceFolder": "/workspaces/${localWorkspaceFolderBasename}",
	"postCreateCommand": "az version",
	"forwardPorts": [3000, 8010, 8020, 8030, 8081],
	"portsAttributes": {
		"3000": {
			"label": "frontend"
		},
		"8010": {
			"label": "backend-pets",
			"visible": "public"
		},
		"8020": {
			"label": "backend-activities",
			"visible": "public"
		},
		"8030": {
			"label": "backend-accessories",
			"visible": "public"
		},
		"8081": {
			"label": "cosmosdb-emulator"
		}
	},
	"features": {
		"ghcr.io/devcontainers/features/azure-cli:1": {},
		"ghcr.io/devcontainers/features/docker-in-docker:2": {}
	},
	"customizations": {
		"vscode": {
			"extensions": [
				"ms-azuretools.vscode-docker",
				"GitHub.copilot",
				"GitHub.copilot-chat",
				"humao.rest-client",
				"GitHub.vscode-pull-request-github",
				"ms-python.python"
			],
			"settings": {
				"editor.formatOnSave": true,
				"github.copilot.enable": {
					"*": true
				},
				"terminal.integrated.defaultProfile.linux": "bash"
			}
		}
	}
}
```

---

*This is a placeholder file. Complete solution will be provided during the workshop.*
