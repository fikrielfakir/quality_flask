# Overview

This is EcoQuality, a comprehensive quality management system for ceramic manufacturing. The application provides end-to-end quality control, energy monitoring, waste management, and compliance tracking specifically designed for ceramic production facilities. It features role-based access control with different permission levels for operators, quality technicians, production managers, and administrators.

The system handles the complete ceramic production lifecycle from lot creation through quality testing, energy consumption monitoring, waste tracking, and regulatory compliance documentation. It includes advanced features like testing campaigns, equipment calibration tracking, and automated alert systems for non-conforming products and energy inefficiencies.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
The frontend is built as a React Single Page Application (SPA) using TypeScript and Vite as the build tool. The architecture follows a component-based design with:

- **UI Components**: Built with Radix UI primitives and shadcn/ui components for consistent design
- **Styling**: Tailwind CSS with a custom design system using HSL color variables
- **State Management**: React Query (@tanstack/react-query) for server state management and caching
- **Routing**: React Router for client-side navigation with protected routes
- **Forms**: React Hook Form with Zod validation for type-safe form handling

The component structure is organized into logical modules (quality control, energy monitoring, waste management, compliance) with shared UI components and utilities.

## Backend Architecture
The backend follows a REST API architecture built with Express.js and TypeScript:

- **Server Framework**: Express.js with middleware for JSON parsing, CORS, and request logging
- **API Design**: RESTful endpoints organized by domain (auth, quality-tests, production-lots, etc.)
- **Request Handling**: Centralized route registration with error handling middleware
- **Development Tooling**: Hot reload with Vite integration for seamless development experience

The server structure separates concerns between routing, business logic (storage layer), and database access.

## Authentication & Authorization
The system implements a comprehensive role-based access control (RBAC) system:

- **Authentication**: Username/password with bcrypt hashing for secure password storage
- **Session Management**: localStorage-based session persistence for the client
- **Authorization**: Role-based permissions with granular access control
- **User Roles**: Admin, Quality Technician, Production Manager, and Operator roles
- **Permission System**: Fine-grained permissions for different system modules and operations

User profiles include department assignment and full audit trails for all user activities.

## Data Storage Solutions
The application uses PostgreSQL as the primary database with Drizzle ORM for type-safe database operations:

- **Database**: PostgreSQL with support for both standard postgres and Neon serverless configurations
- **ORM**: Drizzle ORM with TypeScript schema definitions for type safety
- **Migration System**: Drizzle Kit for database schema migrations
- **Connection Pooling**: Support for both standard postgres and Neon serverless connection pooling

The database schema includes comprehensive tables for production lots, quality tests, energy consumption, waste records, compliance documents, user management, and audit logging.

## Core Business Logic
The system implements several key business domains:

- **Quality Control**: Comprehensive testing framework with dimensional analysis, material property testing, and defect tracking
- **Production Management**: Lot-based production tracking with operator assignment and status management  
- **Energy Monitoring**: Multi-source energy consumption tracking (electricity, gas, solar) with cost analysis and efficiency metrics
- **Waste Management**: Categorized waste tracking with recycling metrics and disposal method tracking
- **Compliance**: Document management for certifications, audit trails, and regulatory reporting

Each domain includes specialized data validation, business rules, and reporting capabilities.

# External Dependencies

## Database Services
- **PostgreSQL**: Primary database for production data, can be hosted on Neon Database or traditional PostgreSQL servers
- **Neon Database**: Serverless PostgreSQL option with WebSocket support for real-time features

## UI Component Libraries
- **Radix UI**: Headless component primitives for accessibility and customization
- **shadcn/ui**: Pre-built component library based on Radix UI with Tailwind CSS styling
- **Lucide React**: Icon library for consistent iconography throughout the application

## Development Tools
- **Vite**: Build tool and development server with hot module replacement
- **TypeScript**: Type safety across frontend and backend
- **Tailwind CSS**: Utility-first CSS framework for styling
- **Drizzle Kit**: Database migration and schema management tool

## Security & Authentication
- **bcrypt**: Password hashing for secure user authentication
- **Input Validation**: Form validation using Zod schemas for type-safe data handling

## Data Fetching & State Management
- **TanStack Query**: Server state management with caching, background updates, and optimistic updates
- **React Hook Form**: Form state management with validation integration

The application is designed to be deployed on platforms like Replit, Vercel, or traditional hosting with Docker containerization support.