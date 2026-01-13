# Django Insider

[![PyPI version](https://badge.fury.io/py/django-insider.svg)](https://badge.fury.io/py/django-insider) [![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT) [![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/) [![Django](https://img.shields.io/badge/Django-3.2%2B-092E20.svg)](https://www.djangoproject.com/)

> **The missing observability dashboard for Django.**

**Django Insider** is a comprehensive observability suite that lives entirely inside your application. It provides a zero-config React dashboard to track performance, debug crashes with interactive stack traces, and detect inefficient database queries—all without sending your data to external third-party services.

---

## ✨ Features

### 📊 The Dashboard
A built-in React SPA (Single Page Application) that gives you a real-time pulse of your application.
* **Velocity Charts:** Visualize traffic spikes and error rates over the last 24 hours.
* **Health Cards:** Instant metrics on Server Errors (500s), Client Errors (400s), and Average Latency.
* **Auto-Refresh:** Data updates automatically every 30 seconds.

### 🕵️ The Investigation Room
A deep-dive debugging interface for crashes.
* **Interactive Stack Trace:** See exactly which file, line, and function caused an error.
* **Context:** View the user, URL, and timestamp associated with the crash.
* **Forensics:** Analyze system logs and database query counts for that specific request.

### 🐢 N+1 Query Detector
Automatically identify performance bottlenecks.
* **Performance Risks:** Flags endpoints executing excessive database queries.
* **Metrics:** Displays Path, Method, and Average Duration for slow views.

### 🔄 Request Replay
* **Footprints:** Detailed logs of every HTTP request (Headers, Body, Response).
* **cURL Generator:** One-click button to generate a `curl` command to instantly reproduce any failed request on your local machine.

---

## 📦 Installation

**1. Install the package via pip:**

```bash
pip install django-insider
```

**2. Add to `INSTALLED_APPS` in `settings.py`:**

```python
INSTALLED_APPS = [
    # ... other apps
    "rest_framework", # Required dependency
    "insider",        # <--- Add this
]
```

**3. Register the Middleware:**

Add the interceptor to your `MIDDLEWARE` list. It is recommended to place it near the top but after `SecurityMiddleware`.

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "insider.middleware.InsiderMiddleware",  # <--- Add this
    # ... other middleware
]
```

**4. Configure URLs:**

Add the Insider dashboard route to your project's `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ...
    path("insider/", include("insider.urls")), # One-line setup
]
```

**5. Run Migrations:**

Create the necessary tables for logging errors and settings.

```bash
python manage.py migrate
```

**6. Access the Dashboard:**

Start your server and visit: `http://localhost:8000/insider/`

---

## ⚙️ Configuration

You can override the default behavior by adding an `INSIDER_CONFIG` dictionary to your `settings.py`.

```python
INSIDER_CONFIG = {
    "CAPTURE_REQUEST_BODY": True,
    "SLOW_REQUEST_THRESHOLD": 500,
    "IGNORE_PATHS": ["/static/", "/health/"],
}
```

### Traffic Filtering & Scope
| Option | Default | Description |
| :--- | :--- | :--- |
| `IGNORE_PATHS` | `['/static/', ...]` | List of URL prefixes to exclude from monitoring. |
| `IGNORE_ADMIN` | `True` | If `True`, ignores all traffic to the Django Admin panel. |
| `CAPTURE_METHODS` | `['GET', ...]` | Whitelist of HTTP methods to record. |

### Data Capture & Privacy
| Option | Default | Description |
| :--- | :--- | :--- |
| `CAPTURE_REQUEST_BODY` | `False` | Saves the raw JSON/Form body. **Warning:** Increases DB usage. |
| `CAPTURE_RESPONSE` | `False` | Saves the response body sent to the client. Keep `False` in production. |
| `MASK_FIELDS` | `['password', ...]` | Keys in headers/body to redact (replace with `********`). |
| `CAPTURE_USER` | `True` | Records the ID/Username of the logged-in user. |

### Performance & Notifications
| Option | Default | Description |
| :--- | :--- | :--- |
| `SLOW_REQUEST_THRESHOLD` | `None` | Latency (in ms) to flag a request as "Slow". |
| `COOLDOWN_HOURS` | `24` | Hours to wait before sending a repeat notification for the same error. |
| `DB_ALIAS` | `'default'` | The database connection name to use for logs. |

---

## 🏗 Architecture

Insider operates on a **Host-Guest** architecture:
* **The Host:** Your Django Project.
* **The Guest:** The `insider` package.

It uses **Celery** to offload heavy logging tasks, ensuring your application's response time is not impacted by monitoring.

1.  **Middleware:** Intercepts the request/response lifecycle.
2.  **Exception Hooks:** Catches unhandled errors and generates "Incidences".
3.  **Async Tasks:** Ships data to the database asynchronously via Celery.
4.  **Embedded Frontend:** A compiled React app served directly by Django views.

---

## 🤝 Contributing

Contributions are welcome!
1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
