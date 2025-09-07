# Ready 2 Dink

## Overview

A Flask-based pickleball matchmaking and tournament platform designed to connect players and facilitate competitive play. The system allows players to register with detailed profiles including personal information and selfie uploads, enter tournaments with automatic deadline management, and track tournament progress through completion. Built with a focus on community trust and accountability through profile verification features.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework for rapid development and simplicity
- **Database**: SQLite for lightweight, file-based data storage without requiring external database server setup
- **Session Management**: Flask's built-in session handling with configurable secret key
- **File Handling**: Local file storage for selfie uploads with security validation

### Data Model
- **Players Table**: Stores comprehensive player profiles including personal details, locations, skill levels, and photo references
- **Tournaments Table**: Tracks tournament entries with automatic deadline calculation (7-day completion window)
- **Relationships**: Foreign key relationship linking tournaments to registered players

### Frontend Architecture
- **Template Engine**: Jinja2 templating for server-side rendering
- **UI Framework**: Bootstrap with dark theme for modern, responsive design
- **Component Structure**: Base template with navigation, extending to specialized pages (dashboard, registration, tournament management)
- **Icons**: Font Awesome integration for consistent visual elements

### File Upload System
- **Security**: Whitelist-based file type validation for image uploads (PNG, JPG, JPEG, GIF)
- **Storage**: Local filesystem storage in static/uploads directory
- **Processing**: Werkzeug secure filename handling to prevent security vulnerabilities

### Authentication & Security
- **Session-based**: Uses Flask sessions for user state management
- **File Security**: Secure filename processing and extension validation
- **Environment Variables**: Configurable session secret for production deployment

### Core Features Architecture
- **Registration Flow**: Multi-field form with file upload capability and database validation
- **Tournament Management**: Automated deadline calculation and status tracking
- **Dashboard System**: Personalized player profiles with tournament history
- **Administrative Interface**: Tournament oversight with completion status management
- **Payout Management System**: Automated tournament winner payout tracking with admin interface

### Payout Management Architecture
- **Automatic Payout Creation**: Tournament winners automatically generate payout records upon completion
- **Multi-Platform Support**: Handles PayPal, Venmo, and Zelle account information for prize distribution
- **Status Tracking**: Complete lifecycle management (pending → processing → paid/failed)
- **Admin Interface**: Comprehensive payout dashboard with bulk processing capabilities
- **Prize Calculation**: Automated calculation based on tournament entry fees (70% prize pool, 30% platform revenue)
- **Financial Tracking**: Monthly totals, outstanding payments, and transaction history

## External Dependencies

### Python Libraries
- **Flask**: Core web framework for routing and request handling
- **Werkzeug**: File upload security and utilities (bundled with Flask)
- **SQLite3**: Built-in Python database interface

### Frontend Dependencies
- **Bootstrap CSS**: Via CDN for responsive design framework
- **Font Awesome**: Via CDN for iconography and visual elements

### Infrastructure
- **File System**: Local storage for uploaded images and SQLite database
- **Static Assets**: Flask's static file serving for uploaded content

### Environment Configuration
- **SESSION_SECRET**: Environment variable for Flask session security
- **Upload Directory**: Configurable local file storage path