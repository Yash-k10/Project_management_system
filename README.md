# ProjectHub

> **Manage Projects. Collaborate. Build Together.**

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Yash-k10/Project_management_system)

A simple, lightweight Project Management System built with Python Flask, SQLite, HTML, CSS, and Vanilla JavaScript.

## Features

- **Authentication**: User registration and login with password hashing (`Werkzeug`).
- **Dashboard**: View personal projects ("My Projects") and community projects ("All Projects").
- **Project Management**: Create projects with title, description, tech stack, and `.zip` source archive upload.
- **Status Tracking**: Update project progress (`Not Started`, `In Progress`, `Completed`).
- **Team Collaboration**: Project owners can invite registered users to collaborate.
- **Access Control & Permissions**:
  - Only owners and invited members can download project archives and participate in project chat.
  - Normal users can view public project information.
- **Project Chat**: Built-in messaging for project members.
- **AI Thesis Generator**: Generates an academic 9-section project thesis (supports OpenAI API with automatic fallback template).
- **Thesis Export**: Download generated thesis as a `.txt` file.

## Tech Stack

- **Backend**: Python, Flask
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, Vanilla JavaScript

## Project Structure

```text
├── app.py
├── requirements.txt
├── database.db (created automatically on startup)
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── create_project.html
│   ├── project.html
│   └── thesis.html
├── static/
│   ├── style.css
│   └── script.js
└── uploads/
```

## Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/Yash-k10/Project_management_system.git
cd Project_management_system
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```

Open your browser and navigate to `http://127.0.0.1:5000`.

### 4. (Optional) AI Thesis Configuration
To use OpenAI for thesis generation, set your API key:

**PowerShell:**
```powershell
$env:OPENAI_API_KEY="your-api-key-here"
```

**Linux / macOS:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

*Note: If no API key is set, the application uses an automatic structured fallback template.*
