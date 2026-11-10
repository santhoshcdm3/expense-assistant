# Expense Assistant (Oracle APEX Integration)

Redesigned AI-powered expense tracking web application with modern Tailwind UI, passcode verification, and Netlify proxy routing to Oracle APEX ORDS endpoints.

## Features
- **Modern Glassmorphic UI**: High-contrast dark theme built with Tailwind CSS and FontAwesome.
- **Natural Date Handling**: Supports inputs like `show yesterday expense` and `show today expense`.
- **Passcode Authentication**: Built-in verification (`1234`) before executing API requests.
- **Netlify Proxying**: Maps relative `/api/*` frontend calls to Oracle APEX REST endpoints (`/add_exp/newexp`, `/gt/expenses`, `/frmto/exp/dates`).

## File Structure
```text
.
├── frontend/
│   └── index.html
├── netlify.toml
└── README.md
```
