# Sheep Farm Management Product Requirements Document (PRD)

## Goals and Background Context

### Goals

-   Enable small and medium farm owners to easily track animals, health events, and farm operations.
-   Support multiple species (bovine, ovine, porcine) and their breeds, with the ability to add more species based on user requests.
-   Provide a clean, intuitive, and affordable alternative to pen-and-paper or overly complex/expensive solutions.
-   Deliver a fast, PWA-based experience with offline support and DB sync.
-   Achieve first real user adoption and usability within 6 months.

### Background Context

Small and medium farm owners often rely on pen and paper or outdated, expensive, or overly complex software to manage their animals and farm operations. Existing digital solutions are either too robust (targeting large enterprises), limited to a single animal type, or lack modern, user-friendly interfaces. This project aims to fill that gap by providing a focused, easy-to-use platform for tracking animals, their health, lineage, and farm events, with a strong emphasis on usability and accessibility for non-technical users. The platform is designed to be extensible, allowing users to request and add new species as their needs evolve.

### Change Log

| Date       | Version | Description       | Author    |
| :--------- | :------ | :---------------- | :-------- |
| 2024-06-11 | 0.1     | Initial PRD draft | John (PM) |

## Requirements

### Functional

-   FR1: Users can register, log in, and manage their account.
-   FR2: Users can create up to 2 farms and join as a member of other farms.
-   FR3: Users can add, edit, and remove animals for supported species (bovine, ovine, porcine).
-   FR4: Users can set animal parents, acquisition details, and track lineage.
-   FR5: Users can record and view animal events (sickness, vaccination, pregnancy, birth, etc.).
-   FR6: Users can request the addition of new species.
-   FR7: The app provides a fast, responsive PWA experience with offline support and syncs data to the database when online.
-   FR8: Users can view and manage breeds for each species.
-   FR9: Users can view farm and animal history.

### Non Functional

-   NFR1: The app must be intuitive and easy to use for non-technical users.
-   NFR2: The app must support offline usage and synchronize data when connectivity is restored.
-   NFR3: The app must be performant on low-end devices and slow connections.
-   NFR4: Data privacy and security must be ensured for all user and farm data.
-   NFR5: The system must be extensible to support new species and features in the future.

## User Interface Design Goals

### Overall UX Vision

-   Mobile-first, intuitive, and clean interface designed for ease of use by non-technical farm owners.
-   Minimize cognitive load with clear navigation, large touch targets, and simple workflows.
-   Fast, responsive interactions with offline support and seamless sync when online.

### Key Interaction Paradigms

-   Simple, step-by-step forms for adding animals, events, and farms.
-   Dashboard overview for quick access to farm and animal status.
-   Contextual actions (e.g., add event from animal profile).
-   Easy switching between farms (if user is part of multiple).

### Core Screens and Views

-   Login/Registration
-   Main Dashboard (farm overview)
-   Animal List & Animal Detail
-   Add/Edit Animal
-   Event Tracking (sickness, vaccination, pregnancy, etc.)
-   Farm Management (add/edit farm, switch farm)
-   Settings/Profile
-   Species/Breed Management
-   Request New Species

### Accessibility

-   Aim for WCAG AA compliance where feasible (high contrast, readable fonts, accessible navigation).

### Branding

-   Friendly, approachable, and modern visual style.
-   Use of farm and animal imagery/icons where appropriate.
-   Branding to be refined post-MVP based on user feedback.

### Target Device and Platforms

-   Mobile-first PWA (Progressive Web App) supporting Android and iOS smartphones.
-   Responsive design for tablet and desktop use, but primary focus is mobile usability.

## Technical Assumptions

### Repository Structure

-   Modular monorepo for backend only; all application code resides in `src/` with clear separation by domain (models, controllers, routes, plugins, etc.).

### Service Architecture

-   Monolithic Fastify server using TypeScript for type safety and maintainability.
-   Sequelize ORM for PostgreSQL (or other SQL DB) with models, migrations, and associations.
-   Strict adherence to modularity and separation of concerns.

### Data Validation

-   Extensive use of JSON Schema and custom validation logic to ensure all incoming data is correct, safe, and user-friendly error messages are provided.
-   Validation is a first-class concern: all endpoints validate input and output data to guide users and prevent errors.

### Testing Requirements

-   Unit tests for all business logic and validation.
-   Integration tests for API endpoints.
-   Manual testing for user flows and edge cases.

### Additional Technical Assumptions and Requests

-   Designed for extensibility: easy to add new modules (e.g., new species, event types).
-   API documentation will be maintained in the `little-sheep` folder using Bruno (a Postman-like tool) for endpoint collections and usage examples.
-   Security best practices (input sanitization, authentication, authorization) are followed throughout.

## Epics

1. Foundation & Core Infrastructure: Establish project setup, modular Fastify backend, database connection, and user authentication.
2. Farm & User Management: Implement farm creation, membership, and user profile management.
3. Animal & Species Management: Enable CRUD for animals, species, and breeds, including parentage and acquisition tracking.
4. Event Tracking & Validation: Add event tracking (sickness, vaccination, pregnancy, etc.) with strong data validation and user guidance.
5. Extensibility & Requests: Allow users to request new species and ensure the system is easy to extend for future needs.
6. Documentation & Testing: Maintain up-to-date Bruno collections in little-sheep, and ensure robust automated and manual testing coverage.

## Epic 1: Foundation & Core Infrastructure

Establish the foundational backend infrastructure, including project setup, modular Fastify server, database connection, and user authentication to enable secure access and future extensibility.

### Story 1.1 Project Setup & Repo Structure

As a developer,
I want a clean, modular project structure with TypeScript, Fastify, and Sequelize configured,
so that the backend is maintainable and easy to extend.

#### Acceptance Criteria

-   1: Project uses TypeScript, Fastify, and Sequelize.
-   2: All code is organized in a modular structure under `src/`.
-   3: Database connection and config are set up and tested.
-   4: Linting, formatting, and basic scripts are in place.

### Story 1.2 User Authentication

As a user,
I want to register, log in, and securely manage my session,
so that my data is protected and only accessible to me.

#### Acceptance Criteria

-   1: Users can register and log in with email and password.
-   2: Passwords are securely hashed.
-   3: JWT or session-based authentication is implemented.
-   4: Auth endpoints are tested and documented in Bruno.

---

## Epic 2: Farm & User Management

Implement core user and farm management, including farm creation, membership, and user profile management.

### Story 2.1 User Profile Management

As a user,
I want to view and update my profile information,
so that my account details are accurate.

#### Acceptance Criteria

-   1: Users can view and update their profile (name, email, language, etc.).
-   2: Input validation and error handling are in place.

### Story 2.2 Farm Creation & Membership

As a user,
I want to create up to 2 farms and join other farms by invitation,
so that I can manage multiple farm operations.

#### Acceptance Criteria

-   1: Users can create up to 2 farms.
-   2: Users can join other farms via invitation.
-   3: Farm membership is tracked and managed.
-   4: All actions are validated and errors are user-friendly.

---

## Epic 3: Animal & Species Management

Enable CRUD for animals, species, and breeds, including parentage and acquisition tracking.

### Story 3.1 Species & Breed Management

As an admin or user,
I want to view, add, and manage species and breeds,
so that the system supports accurate animal classification.

#### Acceptance Criteria

-   1: Users can view all supported species and breeds.
-   2: Admins can add new breeds to existing species.
-   3: Validation prevents duplicates and enforces naming rules.

### Story 3.2 Animal CRUD & Parentage

As a user,
I want to add, edit, and remove animals, including setting parents and acquisition details,
so that my farm records are complete and accurate.

#### Acceptance Criteria

-   1: Users can add, edit, and remove animals for their farms.
-   2: Users can set parent animals and acquisition details.
-   3: All animal data is validated (e.g., birthdate, species, breed).
-   4: Animal lineage is tracked and viewable.

---

## Epic 4: Event Tracking & Validation

Add event tracking (sickness, vaccination, pregnancy, etc.) with strong data validation and user guidance.

### Story 4.1 Event Recording

As a user,
I want to record events (sickness, vaccination, pregnancy, birth, etc.) for animals,
so that I can track animal health and history.

#### Acceptance Criteria

-   1: Users can add events to animals with type, date, and notes.
-   2: Event types are validated and extensible.
-   3: All event data is validated and errors are user-friendly.

### Story 4.2 Event History & Reporting

As a user,
I want to view the history of events for each animal,
so that I can monitor health and make informed decisions.

#### Acceptance Criteria

-   1: Users can view a chronological list of events for each animal.
-   2: Event data is filterable by type and date.
-   3: Data is presented clearly and accessibly.

---

## Epic 5: Extensibility & Requests

Allow users to request new species and ensure the system is easy to extend for future needs.

### Story 5.1 Request New Species

As a user,
I want to request the addition of new animal species,
so that the system can grow with my needs.

#### Acceptance Criteria

-   1: Users can submit requests for new species.
-   2: Requests are tracked and visible to admins.
-   3: Admins can review and approve/deny requests.

### Story 5.2 Extensible Architecture

As a developer,
I want the system to be modular and easy to extend,
so that new features and species can be added with minimal effort.

#### Acceptance Criteria

-   1: Adding new species or event types requires minimal code changes.
-   2: Documentation exists for extending the system.

---

## Epic 6: Documentation & Testing

Maintain up-to-date Bruno collections in little-sheep, and ensure robust automated and manual testing coverage.

### Story 6.1 Bruno API Collections

As a developer,
I want all endpoints documented in Bruno collections,
so that frontend and third-party developers can easily use the API.

#### Acceptance Criteria

-   1: All endpoints are documented in little-sheep using Bruno.
-   2: Example requests and responses are included.

### Story 6.2 Automated & Manual Testing

As a developer,
I want automated and manual tests for all major features,
so that the system is reliable and regressions are caught early.

#### Acceptance Criteria

-   1: Unit and integration tests cover all business logic and endpoints.
-   2: Manual test cases are documented for critical user flows.

## Checklist Results Report

| Item                                     | Status | Notes                        |
| ---------------------------------------- | ------ | ---------------------------- |
| Goals and Background Context defined     | ✅     |                              |
| Requirements (Functional/Non-Functional) | ✅     |                              |
| UI Design Goals documented               | ✅     | Mobile-first, PWA            |
| Technical Assumptions captured           | ✅     | Fastify, Sequelize, modular  |
| Epics and Stories detailed               | ✅     |                              |
| API documentation plan (Bruno)           | ✅     | In little-sheep folder       |
| Testing plan (unit/integration/manual)   | ✅     |                              |
| Extensibility for new species            | ✅     | User request flow included   |
| Accessibility and branding considered    | ✅     | WCAG AA aim, modern/friendly |
| Stakeholder review complete              | ⬜     | To be reviewed               |
