# MicroHack: GitHub for Modern Development

Welcome to the GitHub MicroHack! This hands-on workshop explores modern software development practices using GitHub's comprehensive development platform. Learn how to leverage AI assistance, implement robust DevSecOps practices, and build scalable microservices architectures.

## Workshop Overview

This MicroHack guides you through a comprehensive journey of modern development practices, from basic GitHub concepts to advanced AI-assisted development and enterprise-scale DevSecOps implementation.

This repozitory provides two branches:
- **main** - this is complete repository with solutions
- **student** - starting point for student, this is base for repo template you will be using in a lab

Instructors please read [Teacher README](./teacher/README.md)

### 🎯 Learning Objectives

- Master GitHub's collaborative development features and workflows
- Experience AI-assisted development with GitHub Copilot
- Implement modern CI/CD pipelines with advanced security integration
- Build and deploy microservices using cloud-native technologies
- Understand enterprise-scale development governance and best practices

### 🏗️ Sample Application

The workshop uses a fictious **PetPal** application, a playful microservices‑based application that helps users manage their pets, track activities, and explore accessories. 

![PetPal web app](./docs/app-full.png)

#### Backend Services
- **🐾 Pet Service** (Port 8010) - Core pet management with CRUD operations
- **📊 Activity Service** (Port 8020) - Pet activity tracking and analytics  
- **🛍️ Accessory Service** (Port 8030) - Inventory management for pet accessories (TO BE IMPLEMENTED)

Each service demonstrates modern development practices including:
- RESTful API design with FastAPI
- Azure CosmosDB integration
- Containerization with Docker
- Comprehensive testing strategies
- OpenAPI documentation
- Health monitoring and observability

## 🏆 MicroHack Challenges

This workshop consists of 11 progressive challenges designed to build comprehensive GitHub and modern development expertise:

### Foundation Challenges
| Challenge | Title | Focus Area | Duration |
|-----------|-------|------------|----------|
| [01](/challenges/challenge-01/README.md) | **Access and Identity** | GitHub organization setup, identity management strategies | 30 min |
| [02](/challenges/challenge-02/README.md) | **GitHub Copilot Introduction** | AI-assisted development fundamentals | 45 min |
| [03](/challenges/challenge-03/README.md) | **GitHub Codespaces** | Cloud development environments | 45 min |

### Collaboration and Planning
| Challenge | Title | Focus Area | Duration |
|-----------|-------|------------|----------|
| [04](/challenges/challenge-04/README.md) | **Brainstorming with AI, project management** | Requirements gathering, constitution and standards, project management | 20 min |
| [05](/challenges/challenge-05/README.md) | **GitHub Copilot – From Enabled to Effective** | Copilot best practices, customization and guidance | 30 min |

### Development and Implementation  
| Challenge | Title | Focus Area | Duration |
|-----------|-------|------------|----------|
| [06](/challenges/challenge-06/README.md) | **Design a new microservice with Copilot** | AI-assisted architecture design, specs | 20 min |
| [07](/challenges/challenge-07/README.md) | **Implementation and testing** | Specs-drive development, local testing and integration | 45 min |

### Infrastructure and Deployment
| Challenge | Title | Focus Area | Duration |
|-----------|-------|------------|----------|
| [08](/challenges/challenge-08/README.md) | **Infrastructure as Code** | Azure deployment, security patterns | 45 min |
| [09](/challenges/challenge-09/README.md) | **CI/CD with GitHub Actions** | Automated pipelines, deployment strategies | 45 min |

### Advanced Topics
| Challenge | Title | Focus Area | Duration |
|-----------|-------|------------|----------|
| [10](/challenges/challenge-10/README.md) | **DevSecOps and Governance** | Security integration, compliance automation | 30 min |
| [11](/challenges/challenge-11/README.md) | **AI Agent Automation** | Advanced Copilot agents, task delegation | 20 min |

### 📚 Bonus Challenge (Optional)
| Challenge | Title | Focus Area | Duration |
|-----------|-------|------------|----------|
| [12](/challenges/challenge-12/README.md) | **SRE with AI Agents** | Operational automation, monitoring, troubleshooting | - min |

## 🚀 Quick Start Guide

### Prerequisites
- GitHub account with Copilot access
- Azure subscription (will be provided)
- Basic understanding of software development
- Familiarity with containerization concepts

### Workshop Setup

1. **Access Azure environment** (credentials will be provided, you will have to enroll your account to Microsoft Authenticator)
2. **Login to GitHub Organization** (using your Azure federated identity, details will be provided)

### Environment Setup
No need to set up a local environment; this workshop leverages **GitHub Codespaces** for a cloud-based development environment (instructions part of challenges).

### Starting the Workshop

1. Begin with [Challenge 01](/challenges/challenge-01/README.md)
2. Complete challenges sequentially
3. Use provided solutions as reference when needed
4. Ask instructors for help when stuck

## 🎓 Learning Path and Tips

### Recommended Approach
- **Focus on fundamentals first**: Challenges 1-5 establish core GitHub and Copilot skills
- **Build progressively**: Each challenge builds on previous knowledge
- **Practice extensively**: Use provided sample application for hands-on experience
- **Collaborate actively**: Work with peers, discuss approaches, share learnings

### Success Strategies
- **Leverage AI assistance**: Use Copilot throughout the workshop for faster learning
- **Don't skip testing**: Quality practices are essential for real-world success
- **Understand the 'why'**: Focus on understanding principles, not just completing tasks
- **Document your journey**: Keep notes on learnings and best practices
- **Ask questions**: Instructors and peers are valuable resources

## 📚 Additional Resources

### GitHub Learning Resources
- [GitHub Skills](https://skills.github.com/) - Interactive learning courses
- [GitHub Docs](https://docs.github.com/) - Comprehensive documentation
- [GitHub Community](https://github.community/) - Community support and discussions

### AI-Assisted Development
- [Copilot Documentation](https://docs.github.com/en/copilot)
- [AI Pair Programming Best Practices](https://github.blog/2023-06-20-how-to-write-better-prompts-for-github-copilot/)
- [Responsible AI Development](https://github.com/github/copilot-research)

### DevOps and Cloud
- [Azure DevOps Documentation](https://docs.microsoft.com/en-us/azure/devops/)
- [Microservices Patterns](https://microservices.io/)
- [Cloud Native Computing Foundation](https://www.cncf.io/)

---

**Ready to transform your development workflow?** 
Start with [Challenge 01: Access and Identity](/challenges/challenge-01/README.md) and begin your GitHub mastery journey! 🚀

