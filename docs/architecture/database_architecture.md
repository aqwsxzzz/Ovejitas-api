# Ovejitas API Database Architecture

## Overview

The Ovejitas API is a comprehensive farm management system built with Node.js, Fastify, and Sequelize ORM. It utilizes PostgreSQL as the database engine and implements a well-structured relational database design for managing farms, animals, breeds, species, and measurements.

## Technology Stack

- **Database**: PostgreSQL
- **ORM**: Sequelize v6.37.7
- **API Framework**: Fastify v5.3.2
- **Language**: TypeScript
- **ID Encoding**: Hashids (for public-facing IDs)

## Database Schema

### Core Entities

#### 1. Users (`users`)
Central authentication and user management entity.

**Fields:**
- `id` (INTEGER UNSIGNED, PK, AUTO_INCREMENT)
- `display_name` (STRING, NOT NULL)
- `email` (STRING, NOT NULL, UNIQUE)
- `password` (STRING, NOT NULL)
- `is_active` (BOOLEAN, DEFAULT: true)
- `role` (ENUM: 'user', 'admin', DEFAULT: 'user')
- `language` (ENUM: 'en', 'es', DEFAULT: 'en')
- `last_visited_farm_id` (INTEGER UNSIGNED, FK → farms.id, NULLABLE)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Relationships:**
- Has many FarmMemberships
- Has many AnimalMeasurements (as measurer)

#### 2. Farms (`farms`)
Core entity representing individual farms.

**Fields:**
- `id` (INTEGER UNSIGNED, PK, AUTO_INCREMENT)
- `name` (STRING, NOT NULL)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Relationships:**
- Has many FarmMembers
- Has many Animals
- Has many Invitations

#### 3. Farm Members (`farm_members`)
Junction table implementing many-to-many relationship between Users and Farms with role-based access.

**Fields:**
- `id` (INTEGER UNSIGNED, PK, AUTO_INCREMENT)
- `farm_id` (INTEGER UNSIGNED, FK → farms.id, NOT NULL)
- `user_id` (INTEGER UNSIGNED, FK → users.id, NOT NULL)
- `role` (ENUM: 'owner', 'member', DEFAULT: 'member')
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Relationships:**
- Belongs to Farm
- Belongs to User

#### 4. Species (`species`)
Master species catalog with multilingual support.

**Fields:**
- `id` (INTEGER UNSIGNED, PK, AUTO_INCREMENT)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Relationships:**
- Has many SpeciesTranslations
- Has many Breeds
- Has many Animals

#### 5. Species Translations (`species_translation`)
Provides multilingual names for species.

**Fields:**
- `id` (INTEGER UNSIGNED, PK, AUTO_INCREMENT)
- `species_id` (INTEGER UNSIGNED, FK → species.id, NOT NULL)
- `language_code` (ENUM: 'en', 'es', NOT NULL)
- `name` (STRING, NOT NULL)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Relationships:**
- Belongs to Species

#### 6. Breeds (`breeds`)
Breed information linked to species.

**Fields:**
- `id` (INTEGER UNSIGNED, PK, AUTO_INCREMENT)
- `species_id` (INTEGER UNSIGNED, FK → species.id, NOT NULL)
- `name` (STRING, NOT NULL)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Indexes:**
- UNIQUE INDEX on (`species_id`, `name`)

**Relationships:**
- Belongs to Species
- Has many Animals

#### 7. Animals (`animals`)
Core entity for livestock management.

**Fields:**
- `id` (INTEGER UNSIGNED, PK, AUTO_INCREMENT)
- `farm_id` (INTEGER UNSIGNED, FK → farms.id, NOT NULL)
- `species_id` (INTEGER UNSIGNED, FK → species.id, NOT NULL)
- `breed_id` (INTEGER UNSIGNED, FK → breeds.id, NOT NULL)
- `name` (STRING, NOT NULL)
- `tag_number` (STRING, NOT NULL)
- `sex` (ENUM: 'male', 'female', 'unknown', DEFAULT: 'unknown')
- `birth_date` (DATE, NULLABLE)
- `status` (ENUM: 'alive', 'sold', 'deceased', DEFAULT: 'alive')
- `reproductive_status` (ENUM: 'open', 'pregnant', 'lactating', 'other', DEFAULT: 'other')
- `father_id` (INTEGER UNSIGNED, FK → animals.id, NULLABLE)
- `mother_id` (INTEGER UNSIGNED, FK → animals.id, NULLABLE)
- `acquisition_type` (ENUM: 'born', 'purchased', 'other', DEFAULT: 'other')
- `acquisition_date` (DATE, NULLABLE)
- `weight_id` (INTEGER, FK → animal_measurements.id, NULLABLE)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Indexes:**
- UNIQUE INDEX on (`farm_id`, `species_id`, `tag_number`) WHERE tag_number IS NOT NULL

**Relationships:**
- Belongs to Farm
- Belongs to Species
- Belongs to Breed
- Belongs to Animal (father)
- Belongs to Animal (mother)
- Has many Animals (as father)
- Has many AnimalMeasurements
- Belongs to AnimalMeasurement (latest weight)

#### 8. Animal Measurements (`animal_measurements`)
Tracks various measurements for animals over time.

**Fields:**
- `id` (INTEGER, PK, AUTO_INCREMENT)
- `animal_id` (INTEGER UNSIGNED, FK → animals.id, NOT NULL)
- `measurement_type` (ENUM: 'weight', 'height', 'body_condition_score')
- `value` (DECIMAL(10,2), NOT NULL, MIN: 0)
- `unit` (ENUM: 'kg', 'lbs', 'cm', 'inches', 'score')
- `measured_at` (TIMESTAMP, DEFAULT: NOW)
- `measured_by` (INTEGER UNSIGNED, FK → users.id, NULLABLE)
- `notes` (TEXT, NULLABLE)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Indexes:**
- INDEX on (`animal_id`, `measurement_type`, `measured_at`)
- INDEX on (`measured_at`)

**Relationships:**
- Belongs to Animal
- Belongs to User (measurer)

#### 9. Farm Invitations (`farm_invitations`)
Manages invitations for users to join farms.

**Fields:**
- `id` (INTEGER, PK, AUTO_INCREMENT)
- `email` (STRING, NOT NULL)
- `farm_id` (INTEGER UNSIGNED, FK → farms.id, NOT NULL)
- `role` (ENUM: 'owner', 'member', DEFAULT: 'member')
- `token` (STRING, NOT NULL, UNIQUE)
- `status` (ENUM: 'pending', 'accepted', 'declined', 'expired', DEFAULT: 'pending')
- `expires_at` (TIMESTAMP, NOT NULL)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Relationships:**
- Belongs to Farm

## Entity Relationship Diagram

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│    Users    │────<│  Farm Members    │>────│    Farms    │
└─────────────┘     └──────────────────┘     └─────────────┘
       │                                             │
       │                                             │
       │last_visited_farm_id                        │
       └─────────────────────────────────────────────┘
       │                                             │
       │measured_by                                  │ 
       │                                     ┌───────▼────────┐
       │                                     │  Invitations   │
       │                                     └────────────────┘
       │
       │                    ┌──────────────┐
       └───────────────────<│ Measurements │
                           └──────────────┘
                                    │
                                    │animal_id
                                    ▼
┌─────────────┐     ┌──────────────────┐
│   Species   │────<│     Animals      │>────┐
└─────────────┘     └──────────────────┘     │
       │                    │ │ │             │
       │                    │ │ │father_id/   │
       │species_id          │ │ │mother_id    │
       ▼                    │ │ └─────────────┘
┌─────────────┐             │ │
│Translations │             │ │breed_id      farm_id
└─────────────┘             │ │               │
                           │ ▼               │
┌─────────────┐             │ ┌──────────────┐ │
│   Breeds    │─────────────┘ │    Farms     │<┘
└─────────────┘               └──────────────┘
```

## Key Design Patterns

### 1. Multi-tenancy
The system implements farm-level multi-tenancy where:
- Each farm is isolated from others
- Users can belong to multiple farms through FarmMembers
- Role-based access control (owner/member) at the farm level

### 2. Multilingual Support
Species names support multiple languages through the SpeciesTranslation table, allowing the API to serve content in different languages based on user preferences.

### 3. Temporal Data
Animal measurements are tracked over time, allowing for:
- Historical tracking of weight, height, and body condition
- Trend analysis
- Latest measurement caching (weight_id in animals table)

### 4. Self-referential Relationships
Animals can reference other animals as parents (father_id, mother_id), enabling:
- Genealogy tracking
- Breeding history
- Family tree visualization

### 5. Soft References
The system uses soft references (ON DELETE SET NULL) for:
- Animal parent relationships
- Latest weight measurements
- User who took measurements

### 6. Hard References with Cascading
Cascading deletes are used for:
- Farm deletion removes all farm members and animals
- Species deletion removes all breeds and translations
- Animal deletion removes all measurements

## Security Considerations

1. **ID Obfuscation**: The API uses Hashids to encode numeric IDs in public responses, preventing ID enumeration attacks.

2. **Password Storage**: User passwords are hashed using bcrypt before storage.

3. **Role-based Access**: Farm-level roles (owner/member) control access to resources.

4. **Token-based Invitations**: Secure token generation for farm invitations with expiration.

## Performance Optimizations

1. **Indexed Queries**:
   - Unique compound index on (farm_id, species_id, tag_number) for fast animal lookups
   - Index on measurement queries by type and time
   - Unique index on breed names per species

2. **Latest Measurement Caching**:
   - Animals table includes weight_id for quick access to latest weight without querying measurements table

3. **Efficient Relationships**:
   - Proper foreign key constraints with appropriate cascade behaviors
   - Optimized join queries through Sequelize associations

## Migration Strategy

The database uses Sequelize migrations located in `/src/migrations/` with timestamps to ensure proper ordering:
- User and core entity creation
- Species and translation support
- Farm member relationships
- Breed and animal models
- Measurement tracking system
- Constraint updates and optimizations

## Future Considerations

1. **Scalability**: Current design supports horizontal scaling at the application level with shared PostgreSQL instance.

2. **Audit Trail**: Consider adding audit tables for tracking changes to critical entities.

3. **Archival**: Implement archival strategy for historical data (deceased animals, old measurements).

4. **Advanced Analytics**: Design supports future analytics features for breeding programs, health tracking, and productivity metrics.