# Vibe Coding Platform

## What This Is

This is a **vibe coding** project — a non-technical business user is building an application with the help of an AI coding agent (you). The user describes what they want in plain language. You handle all technical decisions, code generation, and implementation.

The user does **not** have a programming background. Communicate in simple, clear terms. Avoid jargon unless explaining it. When asking clarifying questions, frame them around the user's business intent, not technical trade-offs.

## How Development Works

This project uses **speckit** to structure the development process. The workflow is:

1. **Constitution** (`principles.md`) — Coding guidelines are already defined. Run `speckit.constitution` with `principles.md` as input to initialize the project constitution. This is done once at project start.

2. **Specification** (`speckit.specify`) — The user describes a feature in their own words. You run `speckit.specify` to turn their description into a structured feature specification. Ask clarifying questions if the description is ambiguous.

3. **Planning** (`speckit.plan`) — You run `speckit.plan` with `tech.md` as the tech stack input. This generates the implementation plan based on the platform's architecture and available resources.

4. **Tasks** (`speckit.tasks`) — Generate the task breakdown from the plan.

5. **Implementation** (`speckit.implement`) — Execute the tasks to build the feature.

The user's only required input is the **feature description** (step 2). Everything else — the tech stack, coding principles, platform constraints — is pre-configured in this repository.

If the speckit toolkit is not installed inside of the project, the basic ideas should still be followed.

## Pre-Configured Files

| File | Purpose | Who wrote it |
|---|---|---|
| `CLAUDE.md` | This file — project context for the AI agent | AI Team |
| `tech.md` | Technical reference: architecture, GCP resources, tech stack, Dockerfile patterns, deployment rules | Senior developer |
| `principles.md` | Coding principles fed into `speckit.constitution` | Architecture |

**Do not contradict these files.** They encode platform constraints that ensure the application is deployable. If the user requests something that conflicts with `tech.md` (e.g., a different database, a separate frontend deployment), explain the constraint and propose an alternative that works within the platform.

## Project Inputs

The platform team provides one values when provisioning the GCP project; the ID of the GCP project (GCP_PROJECT_ID). The other two ENV variables can be deduced from the project ID. GCS_BUCKET is always bkt-gcp-<PROJECT_ID>-<PROJECT_NAME>. The serive account is sa-gcp-<PROJECT_NAME>@<PROJECT_ID>.iam.gserviceaccount.com

| Input | Purpose | Example |
|---|---|---|
| `GCP_PROJECT_ID` | GCP project ID — goes into `container/config.env` | l-plat-gencode-myapp |
| `GCS_BUCKET` | Cloud Storage bucket name — goes into `container/config.env` | bkt-gcp-l-plat-gencode-myapp-myapp |
| `SA_NAME` | Service account email — used locally for `gcloud` impersonation, never in the container | sa-gcp-myapp@l-plat-gencode-myapp.iam.gserviceaccount.com |

These values are filled into `container/config.env` (for `GCP_PROJECT_ID` and `GCS_BUCKET`) at project setup. The app reads them via `pydantic-settings`. No secrets, no key files.

**If `config.env` is empty or the project inputs are missing, ask the user to provide them before proceeding with implementation.** The user received these values from the platform team when their GCP project was provisioned.

## Key Platform Facts

- The application deploys to **Google Cloud Run** as a **single Docker container** on port **8080**.
- All source code lives inside the **`/container`** folder.
- The GCP project is pre-provisioned with resources via Terraform. **Not all resources need to be used** — choose only what the feature requires:
  - **Firestore** — optional NoSQL database for structured data
  - **Cloud Storage** — optional file/blob storage
  - **Vertex AI** — optional LLM/GenAI capabilities (Gemini)
- User authentication is handled by **IAP** (Identity-Aware Proxy). The app reads user identity from the `X-Goog-Authenticated-User-Email` header. Do not implement login flows.
- If the app needs admin roles, use a Firestore `admins` collection. The **first user** to access the app is **automatically made admin** when the collection is empty.
- Project configuration (`GCP_PROJECT_ID`, `GCS_BUCKET`) lives in **`container/config.env`**, which is copied into the container and loaded by the app at startup.
- All GCP authentication uses **Application Default Credentials (ADC)**. No key files, no secrets. Locally, the developer impersonates the service account via `gcloud`.
- CI/CD is automatic — pushing to `feature/*` or merging to `develop` triggers deployment.
- **Branch naming:** All work branches MUST be named `feature/<name>` (e.g., `feature/001-my-feature`). CI/CD only triggers on branches matching the `feature/*` pattern. Before pushing, verify you are on a `feature/` branch. If speckit or any script created a branch with a different name, rename it to `feature/<name>` before pushing.

## Working with the User

- The user thinks in terms of **what the app should do**, not how it should be built. Translate their intent into technical implementation.
- When proposing features or asking questions, use **business language**: "Should any user be able to delete entries, or only admins?" not "Should we add RBAC with role-based middleware?"
- If unsure about a requirement, **ask**. A quick question now prevents a rewrite later.
- Show progress visually when possible — describe what the app will look like, how users will interact with it.
- Keep the user informed at milestones: "The backend API is ready, now I'll build the UI."