# Challenge 10: Approval Processes and DevSecOps Elements

## Overview

At this point we simply accept commits to our main branch and automatically deploy. In this challenge we will focus on adding automated checks before accepting changes and also introduce simple approval workflow to deploy to production environment.

## Pull request
A Pull Request (PR) is a mechanism in version control systems like GitHub that allows developers to notify team members that they have completed a feature or bug fix and want to merge their changes into the main codebase. It serves as a dedicated forum for discussing the proposed changes, conducting code reviews, and ensuring quality checks are passed before the code is integrated.

### Task 1: Enforce policies
Use rules in your repository settings to enforce:
- Enable Copilot Code Review to be automatically run on each Pull Request
- No commits directly to main, only throw Pull Request
- At least 1 approval before merging

### Task 2: Test Pull Request
Test Pull Request and see code review:
1. Create new branch, my-patch-1
2. Introduce some change in code (for example just copy `main.py` into `main-delete-1.py` just to test things out.) and commit
3. Create Pull Request
4. Go to GitHub.com and see Pull Request - read code review from Copilot, try discussions, than approve and merge and delete branches

### Task 3: Add tests and automation
Before accepting any changes we might want to run some tests - is proposed changed secure (run code analysis), follows coding style and best practices, does it compile? We might also want to run automated tasks such as generating documentation (Documentation as Code) or exporting OpenAPI specs and so on.

Use Copilot to add some very basic unit test using pytest and try locally first.

Then create GitHub Actions workflow that is triggered on Pull Request to `main` with `pytest` unit tests.


### Task 4: Enable built-in GitHub Code Quality scanning
Follow guide: [https://docs.github.com/en/code-security/code-quality/how-tos/enable-code-quality](https://docs.github.com/en/code-security/code-quality/how-tos/enable-code-quality)

Update your repository policy to include `Require code quality results`

After few minutes introduce another change, for example just copy `main.py` into `main-delete-3.py` just to test things out.

See results.

## Deployment environments
At this point when code tests are fine (quality, security, ...) we allow merging this to main and deploy into Azure automatically. With **trunk-based development** we can have following strategy:
- Whatever is merged into **main** is deployed into test environment
- Then we can have **pre-prod** environment that is used by are lighthouse clients for testing their integrations and by our beta-testers. We do not want to deploy there automatically, this will require approval, but it is still part of our **main** branch.
- For production we will have one **release** branch from which our production environmnet is deployed. Merging into this branch requires more security adn quality checks as well some additional tests. This is not in scope for our MicroHack.

As part of our release pipelines for services implement **pre-prod** environment. This would contain separate infrastructure deployed by Bicep, in our scenario we will just **mock** this deployment for now. Purpose it to test envs and approvals.

Implement this using GitHub Environments feature: [https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments) and with **Required reviewers**. Run pipeline and see how approval works.


## Optional: GitHub Code Security
So far we focused on code quality and review, but we can leverage **GitHub Code Security** to implement full-scale **DevSecOps**.

This part is optional, ask facilitator to assign license to your repo and continue based on documentation: [https://github.com/security/advanced-security/code-security](https://github.com/security/advanced-security/code-security)