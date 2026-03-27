# Blue Falcon - Airport Operations Platform

A modern, real-time airport operations dashboard built with Django, featuring flights management, gate assignments, staff coordination, and live notifications.

![Blue Falcon](https://img.shields.io/badge/Version-1.0.0-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Django](https://img.shields.io/badge/Django-5.2-green)

## 🚀 Features

### Core Modules
- **Operations Dashboard** - Real-time overview of all airport activities
- **Flights & Gates** - Complete flight schedule and gate assignment management
- **Reports & Analytics** - Generate operational reports and export data
- **User Management** - Role-based access control and team organization

### Technical Features
- Real-time WebSocket notifications
- REST API with OpenAPI documentation
- Secure authentication (2FA-ready)
- Responsive design for all devices
- Production-ready deployment configuration

## 🛠 Tech Stack

### Backend
- **Django 5.2** - Core framework with ORM, admin, auth
- **Django REST Framework** - API development
- **Channels** - WebSocket support for real-time features
- **Daphne** - ASGI server for WebSockets

### Frontend
- **HTML5** - Semantic markup
- **CSS3** - Custom styles with CSS variables
- **Vanilla JavaScript** - No frameworks, pure JS

### Infrastructure
- **WhiteNoise** - Static file serving
- **Gunicorn** - WSGI HTTP server
- **PostgreSQL** - Relational database

## 📦 Installation

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- Node.js 18+ (optional, for development)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/AlexBiobelemo/Project-Falcon.git
   cd Project-Falcon
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database**
   ```bash
   # Create PostgreSQL database
   createdb blue_falcon
   
   # Update settings.py with your database credentials
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Landing Page: `http://localhost:8000`
   - Admin Panel: `http://localhost:8000/admin`
   - API Docs: `http://localhost:8000/api/docs/`

## 🎨 Landing Pages

| Page | Description | URL |
|------|-------------|-----|
| **Home** | Main portfolio-style landing page | `/` |
| **Product Tour** | Interactive module walkthrough | `/app.html` |
| **Tech Stack** | Technology details | N/A (merged) |

## 📱 Responsive Design

The landing pages are fully responsive with breakpoints at:
- **Desktop**: >1200px
- **Tablet**: 900px - 1200px (2-column layouts, hamburger menu)
- **Mobile**: <900px (1-column, hamburger menu)

## 🔐 Demo Access

The live demo includes sample data for testing:

**Credentials:**
- Username: `alex`
- Password: `12345`

## 📁 Project Structure

```
falcon_lp/
├── index.html          # Main landing page
├── app.html            # Product tour page
├── css/
│   └── styles.css      # All styles (2,266 lines)
├── js/
│   └── main.js         # Interactions (417 lines)
├── assets/
│   ├── cloud-wisp-1.svg
│   └── cloud-wisp-2.svg
└── README.md           # This file
```

## 🎯 Key Interactions

### Radar Visual (Hero Section)
- Circular radar display with live aircraft tracking
- 4 aircraft blips with flight labels
- Animated sweep effect (4s cycle)
- Moving blip with flight path animation
- Real-time stats overlay

### Module Timeline
- Horizontal flow layout (desktop)
- 2-column grid (tablet)
- Vertical stack (mobile)
- Hover effects on icons and cards

### Mobile Navigation
- Hamburger menu (<900px)
- Slide-in from right
- Close on link click or outside click
- Smooth animations

## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG = False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up HTTPS/SSL
- [ ] Configure static files (WhiteNoise)
- [ ] Set up database backups
- [ ] Configure logging
- [ ] Set up monitoring (health checks)

### Environment Variables
```bash
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

## 📊 Performance

- **No external frameworks** - Pure vanilla JS
- **Optimized animations** - GPU-accelerated transforms
- **Lazy initialization** - Intersection Observer for animations
- **Passive event listeners** - Better scroll performance
- **Minimal dependencies** - Only Google Fonts

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

**Alex Alagoa Biobelemo**

- GitHub: [@AlexBiobelemo](https://github.com/AlexBiobelemo)
- LinkedIn: [Alex Alagoa Biobelemo](https://www.linkedin.com/in/alex-alagoa-biobelemo/)
- Portfolio: [alexbio.onrender.com](https://alexbio.onrender.com)
- Email: alexbio0405@gmail.com

## 🔗 Links

- **Live Demo**: [blue-falcon.onrender.com](https://blue-falcon.onrender.com)
- **Source Code**: [github.com/AlexBiobelemo/Project-Falcon](https://github.com/AlexBiobelemo/Project-Falcon)
- **Documentation**: API docs available at `/api/docs/`

---

Built with ❤️ using Django & modern web technologies
