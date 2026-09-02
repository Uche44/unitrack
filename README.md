# UniTrack

<div align="center">

**A Final-Year Project Management Platform with AI-Powered Supervisor Tools**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6.svg)](https://www.typescriptlang.org/)

</div>

---

## Overview

UniTrack is a full-stack web application designed to streamline the management of final-year academic projects in nigerian universities. It provides role-based dashboards for students, supervisors, and administrators, with integrated AI tools (via WebMCP) to assist admin in matching students to supervisors based on interests, supervisors in spotting feedback trends across their supervisees, detecting students who are lagging behind, and students in generating defense questions and comparing their performance across others.

### Key Capabilities

- **Role-Based Access**: Separate dashboards for Students, Supervisors, and Admins
- **Project Lifecycle Management**: From proposal submission to final report approval
- **Submission Version Control**: Track revisions with diff comparison
- **Supervisor-Student Matching**: AI-assisted recommendations based on expertise and workload
- **Stalled Student Detection**: Automatic flagging of inactive students (10+ days)
- **Defense Preparation**: AI-generated questions from project content
- **Cohort Benchmarking**: Anonymized progress comparison (opt-in)
- **Feedback Analysis**: Identify recurring themes across student submissions

---

## Tech Stack

### Backend
| Component | Technology |
|-----------|------------|
| Framework | Django 5.2 + Django REST Framework 3.16 |
| Authentication | JWT (djangorestframework-simplejwt) |
| Database | SQLite (dev) / PostgreSQL (production) |
| File Storage | Cloudinary |
| PDF Processing | pypdf 6.7.0 |
| Server | Gunicorn |

### Frontend
| Component | Technology |
|-----------|------------|
| Framework | React 19 + TypeScript 5.9 |
| Build Tool | Vite 7 |
| Styling | Tailwind CSS 4 |
| State Management | Zustand 5 |
| Routing | React Router 7 |
| HTTP Client | Axios |
| Forms | React Hook Form + Zod |
| Testing | Vitest + React Testing Library |
| AI Integration | WebMCP (use-webmcp-tool) |

---

## Project Structure

```
unitrack-combined/
├── unitrack-backend/           # Django REST API
│   ├── accounts/               # User management & authentication
│   ├── projects/               # Project & submission logic
│   ├── unitrack/               # Django settings
│   ├── requirements.txt
│   └── manage.py
│
├── unitrack-frontend/          # React + TypeScript frontend
│   ├── src/
│   │   ├── pages/              # Route pages (dashboards, auth)
│   │   ├── components/         # Reusable UI components
│   │   ├── lib/                # API client, WebMCP tools
│   │   └── context/            # Zustand state
│   ├── package.json
│   └── vite.config.ts
│
├── scripts/                    # Quality gate scripts
├── DEVELOPMENT.md              # Detailed setup guide
├── MILESTONES.md               # Implementation milestones
└── agents.md                   # WebMCP integration spec
```

---

## Prerequisites

- **Python** 3.11+
- **Node.js** 18+
- **npm** or **yarn**
- **Cloudinary account** (for file storage)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/unitrack.git
cd unitrack/unitrack-combined
```

### 2. Backend Setup

```bash
cd unitrack-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (see Environment Variables section)
# Then run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

### 3. Frontend Setup

```bash
cd ../unitrack-frontend

# Install dependencies
npm install

# Create .env file (see Environment Variables section)

# Start development server
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api

---

## Environment Variables

### Backend (`unitrack-backend/.env`)

```env
# Cloudinary (File Storage)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Django Settings
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Admin User (created on first run)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=secure_password
ADMIN_FULL_NAME="Departmental Admin"

# Production only
# DATABASE_URL=postgres://user:password@host:port/dbname
# SECRET_KEY=your-secret-key
```

### Frontend (`unitrack-frontend/.env`)

```env
VITE_API_URL=http://localhost:8000/
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/signup/` | User registration |
| POST | `/api/login/` | Login (returns JWT) |
| POST | `/api/refresh/` | Refresh access token |
| POST | `/api/logout/` | Logout |
| GET | `/api/auth/me/` | Get current user |

### Projects & Submissions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/projects/session/` | List/create sessions |
| POST | `/api/projects/create/` | Create project |
| GET | `/api/projects/` | List projects |
| GET/POST | `/api/submissions/` | List/create submissions |
| POST | `/api/submissions/<id>/action/` | Approve/reject |
| GET | `/api/submissions/<id>/diff/` | Compare versions |

### WebMCP AI Tools
| Endpoint | Role | Description |
|----------|------|-------------|
| `/api/feedback-themes/` | Supervisor | Analyze recurring feedback |
| `/api/stalled-students/` | Admin, Supervisor | Detect inactive students |
| `/api/suggest-supervisor/` | Admin | Supervisor matching |
| `/api/defense-questions/` | Student | Generate defense questions |
| `/api/cohort-benchmark/` | Student | Progress comparison |

---

## User Roles & Workflows

### Student
1. Register with matric number and project interests
2. Wait for supervisor assignment (Admin)
3. Create project proposal
4. Submit milestones: Proposal → Chapter 1 → Chapter 2 → Final Report
5. Receive feedback and revise as needed
6. Generate defense preparation questions

### Supervisor
1. Register with staff ID and areas of expertise
2. Wait for approval (Admin)
3. Review student submissions
4. Approve/reject with feedback
5. Log student contacts (meetings, messages)
6. Analyze recurring feedback themes
7. Detect stalled students

### Admin
1. Approve supervisor registrations
2. Assign supervisors to students
3. Create and manage academic sessions
4. Monitor supervisor workload
5. View stalled students across system

---

## WebMCP AI Tools

UniTrack integrates 6 AI-powered tools via WebMCP that browser-based AI assistants can invoke:

| Tool | Role | Purpose |
|------|------|---------|
| `get_recurring_feedback_themes` | Supervisor | Identify patterns in feedback across students |
| `explain_chapter_changes` | Supervisor | Compare submission versions and feedback coverage |
| `find_stalled_students` | Admin, Supervisor | Flag students with no activity in 21+ days |
| `suggest_supervisor_assignment` | Admin | Match students to supervisors by expertise/workload |
| `generate_defense_questions` | Student | Create defense prep questions from project |
| `compare_my_progress` | Student | Anonymized cohort benchmarking (opt-in) |

All tools are **read-only** and require server-side role verification.

---

## Database Models

### Core Models

- **User**: Custom user model with role-based fields (student/supervisor/admin)
- **ProjectSession**: Academic session with active state enforcement
- **Project**: Student project with supervisor and status tracking
- **Submission**: Milestone submissions with version control
- **SubmissionReview**: Immutable review history
- **SupervisorContact**: Contact logging between supervisors and students
- **Tag**: Expertise/interest tags

---

## Testing

### Backend Tests

```bash
cd unitrack-backend
python manage.py test
python manage.py test accounts.tests  # Specific module
```

### Frontend Tests

```bash
cd unitrack-frontend
npm test              # Run tests
npm run test:watch    # Watch mode
npm run test:coverage # Coverage report
```

### Quality Gates

```powershell
# Run all checks (backend + frontend)
powershell -ExecutionPolicy Bypass -File scripts\run-all-checks.ps1
```

---

## Scripts

### Frontend (npm)
| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Production build |
| `npm run lint` | ESLint check |
| `npm test` | Run tests |

### Backend (Django)
| Command | Description |
|---------|-------------|
| `python manage.py runserver` | Start dev server |
| `python manage.py migrate` | Apply migrations |
| `python manage.py test` | Run tests |
| `python manage.py check` | System check |

---

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style
- Follow PEP 8 for Python
- Follow ESLint rules for TypeScript/React
- Write tests for new features
- Update documentation as needed

---

## Roadmap

- [ ] Email notifications for submission reviews
- [ ] Real-time chat between supervisors and students
- [ ] Calendar integration for deadlines
- [ ] Plagiarism detection integration
- [ ] Mobile application
- [ ] Advanced analytics dashboard

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Django REST Framework for the robust API framework
- React team for the excellent frontend library
- Cloudinary for file storage solutions
- All contributors who help improve UniTrack

---

## Support

If you encounter any issues or have questions:

1. Check the [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup instructions
2. Open an issue on GitHub with detailed information
3. Contact the maintainers

---

<div align="center">

**Built for academic excellence**

</div>
