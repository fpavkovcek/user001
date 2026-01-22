# Challenge 03: Working in GitHub Codespaces Development Environment

## Overview

In this challenge, you'll set up and customize a cloud-based development environment using GitHub Codespaces for the PetPal application. You'll learn how to fork a repository, create a Codespace, and customize it with essential development tools and VS Code extensions. This demonstrates how development environments can be defined as code, making onboarding faster and environments consistent across your team.

## Introduction to GitHub Codespaces

**What are GitHub Codespaces?**

GitHub Codespaces is a cloud-based development environment hosted by GitHub. Each codespace runs in a Docker container on a virtual machine, providing you with a fully configured development environment accessible from your browser or VS Code.

**Key Benefits:**

- **Instant Setup**: Start coding in seconds without installing tools locally
- **Consistent Environments**: Every team member gets the same configuration
- **Configuration as Code**: Dev container configurations are versioned with your code
- **Access Anywhere**: Work from any machine with just a browser
- **Powerful Resources**: Choose from 2 to 32 cores based on your needs
- **Free Tier Available**: Personal accounts include monthly free usage hours

**How It Works:**

1. Codespaces are based on dev container configurations (`.devcontainer/devcontainer.json`)
2. You can customize the base image, install tools, and configure VS Code extensions
3. Changes to the configuration are versioned in your repository
4. When someone creates a new Codespace, they automatically get your customizations

[Learn more about GitHub Codespaces](https://docs.github.com/en/codespaces/overview)

## Learning Objectives

- Understand cloud-based development environments and their benefits
- Learn to configure and customize GitHub Codespaces
- Experience Configuration-as-Code for development environments
- Set up a reproducible development environment for the PetPal application
- Add Azure CLI, Docker, and essential VS Code extensions

## Prerequisites

- GitHub account with Codespaces access (free tier available)
- Basic familiarity with VS Code interface
- Understanding of containerization concepts (helpful but not required)

## Tasks

### Task 1: Access the Repository

You have created repository from template in challenge 01.

### Task 2: Explore the Current Environment

1. **Familiarize Yourself with the Codespace**
   - Notice the VS Code interface running in your browser (or desktop VS Code if you chose that option)
   - Explore the file structure in the Explorer panel
   - Open a terminal (Terminal → New Terminal)
   
2. **Test dafault environment**
   - Check which tools are pre-installed:
     ```bash
     python --version
     node --version
     git --version
     ```

3. **Examine Current Configuration**
   - Look for `.devcontainer` folder (if it exists)
   - Note what extensions are currently installed
   - Document what's missing for Azure development

> **Hint**: Not all repositories come with a dev container configuration. You may need to create one!

### Task 3: Add Azure CLI and Docker-in-Docker Features

1. **Create or Modify Dev Container Configuration**
   - Create `.devcontainer/devcontainer.json` if it doesn't exist
   - Add Azure CLI feature to the configuration
   - Add Docker-in-Docker feature for container operations
   
   > **Hint**: Dev container features are reusable configuration packages. Look for:
   > - Azure CLI feature: `ghcr.io/devcontainers/features/azure-cli:latest`
   > - Docker-in-Docker feature: `ghcr.io/devcontainers/features/docker-in-docker:latest`
   >
   > Features go in the `"features"` section of your `devcontainer.json`

2. **Configure the Base Image**
   - Choose an appropriate base image (Python-based recommended for PetPal)
   - Consider using: `mcr.microsoft.com/devcontainers/python:3.11`

### Task 4: Add Essential VS Code Extensions

Add the following extensions to your dev container configuration to enhance your development experience:

- **ms-azuretools.vscode-docker**: Work with Docker containers and images
- **GitHub.copilot**: AI-powered code completion
- **GitHub.copilot-chat**: AI pair programming assistant
- **humao.rest-client**: Test HTTP APIs directly from VS Code
- **GitHub.vscode-pull-request-github**: Manage pull requests without leaving the editor
- **ms-python.python**: Python language support and debugging

> **Hint**: Extensions are added in the `"customizations"` section under `"vscode"` → `"extensions"` as an array of extension IDs.

### Task 5: Rebuild and Verify Your Configuration

1. **Rebuild the Codespace**
   - After saving your configuration changes
   - Open the Command Palette (Cmd/Ctrl + Shift + P)
   - Type "Codespaces: Rebuild Container"
   - Select it and wait for the rebuild to complete

2. **Verify Installations**
   - Open a new terminal
   - Test Azure CLI:
     ```bash
     az --version
     ```
   - Test Docker:
     ```bash
     docker --version
     ```
   - Check that your extensions are installed (look in the Extensions panel)

3. **Test the PetPal Services**
   - Navigate to one of the backend services
   - Try running it with the newly available tools
   - Use the REST Client extension to test API endpoints (if you created `.http` files)

### Task 6: Document and Commit Your Changes

1. **Test Your Configuration**
   - Create a new Codespace to ensure your configuration works from scratch
   - Delete the old Codespace to save resources
   - Verify all tools and extensions load automatically

2. **Commit Your Configuration**
   - Stage your `.devcontainer` changes
   - Write a clear commit message describing the improvements
   - Push to your forked repository

## Success Criteria

- [ ] Successfully forked the MicroHack-GitHub repository
- [ ] Created and launched a GitHub Codespace
- [ ] Explored the PetPal application structure
- [ ] Created or modified `.devcontainer/devcontainer.json` with:
  - [ ] Azure CLI feature
  - [ ] Docker-in-Docker feature
  - [ ] Six essential VS Code extensions
- [ ] Rebuilt the Codespace with new configuration
- [ ] Verified Azure CLI is working (`az --version` succeeds)
- [ ] Verified Docker is working (`docker --version` succeeds)
- [ ] Confirmed all extensions are installed
- [ ] Tested configuration by creating a fresh Codespace
- [ ] Committed and pushed dev container configuration

## Key Concepts to Understand

- **Configuration as Code**: Development environments defined in version-controlled files
- **Dev Container Features**: Reusable packages for adding tools (Azure CLI, Docker, etc.)
- **Reproducibility**: Every developer gets identical setup automatically
- **Cloud-Native Development**: Full development environment in the cloud
- **Container-Based Isolation**: Each Codespace runs in its own container
- **Instant Onboarding**: New team members productive in minutes, not days

## Tips and Best Practices

- **Resource Management**: Stop or delete Codespaces when not in use to conserve free tier hours
- **Extension Selection**: Only include extensions the whole team needs in the dev container
- **Base Image Choice**: Pick images that match your primary language/runtime
- **Feature Documentation**: Azure CLI and Docker features are documented at [containers.dev/features](https://containers.dev/features)
- **Testing Changes**: Always test your dev container configuration in a fresh Codespace

## Troubleshooting

**Codespace won't start?**
- Check your `devcontainer.json` syntax (valid JSON required)
- Verify feature names and versions are correct
- Look at the creation logs for specific errors

**Azure CLI not found after rebuild?**
- Ensure the feature is in the `"features"` object
- Check spelling and format of the feature reference
- Try a full rebuild rather than just reopening

**Extensions not installing?**
- Verify extension IDs are correct (find them in VS Code Marketplace)
- Check they're under `customizations.vscode.extensions`
- Some extensions require specific base images

## Additional Resources

- [GitHub Codespaces Documentation](https://docs.github.com/en/codespaces)
- [Dev Containers Specification](https://containers.dev/)
- [Available Dev Container Features](https://containers.dev/features)
- [Azure CLI in Codespaces](https://docs.github.com/en/codespaces/developing-in-codespaces/using-github-codespaces-with-azure-cli)
- [VS Code Extension Marketplace](https://marketplace.visualstudio.com/vscode)

## Next Steps

After completing this challenge, you'll have a fully configured cloud development environment for the PetPal application. In future challenges, you'll use this environment to implement features, test APIs, and deploy to Azure - all without needing to install anything locally!

## Solution

[Solution Steps](/solutions/challenge-03/README.md)