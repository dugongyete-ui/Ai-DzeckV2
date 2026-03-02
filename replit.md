# Dzeck AI — Compressed Project Summary

## Overview
Dzeck AI is a web-based AI Agent platform designed to provide an intelligent AI assistant capable of web browsing, shell command execution, file management, and real-time activity display via a VNC viewer. The project aims to deliver a robust and interactive AI experience, leveraging advanced AI models and a modern web stack.

## User Preferences
Not specified in the original document.

## System Architecture

**Architectural Flow:**
The system operates by receiving user messages from the Frontend (Vue 3). These requests are processed by the Backend (FastAPI), which initiates an AI Agent (PlanActFlow). The AI Agent utilizes various tools (Shell, Browser, File, Search) through a Sandbox API. Real-time results and activities are streamed back to the Frontend via Server-Sent Events (SSE), while session states are persisted in MongoDB and cached in Redis.

**Core Technologies & Frameworks:**
-   **Frontend:** Vue 3, TypeScript, Vite, Tailwind CSS, ShadcnUI for a modern, responsive UI.
-   **Backend:** Python 3.11, FastAPI, Beanie ODM for efficient API handling and database interactions.
-   **AI/LLM:** Pollinations AI (`https://text.pollinations.ai/v1`, model `openai-fast`) for core AI capabilities, including streaming responses and image generation.
-   **Sandbox:** A virtual environment running Supervisord, Xvfb, Chromium, x11vnc, websockify, and a FastAPI agent, enabling the AI to interact with a browser and execute commands. An alternative E2B cloud sandbox is available.
-   **Authentication:** JWT-based system with access and refresh tokens, bcrypt for password hashing. Supports `password` mode for user registration and `local` mode for admin credentials.
-   **Internationalization (i18n):** Supports Bahasa Indonesia (default), English, and Mandarin, with locale stored in `localStorage`.
-   **Deployment:** Optimized for Replit's VM deployment target, with `start.sh` managing service initialization for Frontend, Backend, and Sandbox.

**UI/UX Decisions:**
-   **Branding:** The project has been rebranded from "Manus" to "Dzeck AI," including logo, text, and locale storage keys.
-   **Components:** Utilizes ShadcnUI for UI components, Monaco Editor for code display, and noVNC for embedded VNC viewing.
-   **Localization:** Default language is Bahasa Indonesia, with comprehensive translations for UI strings.

**Feature Specifications:**
-   **Chat & Sessions:** Users can create and manage chat sessions with the AI.
-   **File Management:** Upload, list, and export files within a session (as ZIP).
-   **AI Tools:** AI can use shell, browser, file operations, and web search.
-   **Real-time Interaction:** SSE for streaming AI responses and VNC for live sandbox visualization.
-   **Image Generation:** Integration with Pollinations AI for image generation.
-   **Notifications:** Web Notifications API for task completion alerts.

## External Dependencies

-   **Database:** MongoDB Atlas (cloud database)
-   **Cache/Queue:** Redis Labs (cloud cache/queue)
-   **AI/LLM Provider:** Pollinations AI (for `openai-fast` model and image generation)
-   **Cloud Sandbox:** E2B (alternative sandbox provider)
-   **Background Jobs:** Inngest (for orchestrating background tasks like agent-task events)
-   **VNC Client:** noVNC (embedded in the frontend)
-   **Code Editor:** Monaco Editor