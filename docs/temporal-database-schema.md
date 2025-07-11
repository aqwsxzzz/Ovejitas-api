# Temporal Database Schema Design

## Overview
This document defines the database schema for implementing historical tracking capabilities in the Ovejitas animal management system, building on the existing Fastify/Sequelize/PostgreSQL architecture.

## Design Principles

### 1. Hybrid Temporal Architecture
- **Current State**: Maintain existing `animals` table for performance
- **Historical Data**: New temporal tables for time-series tracking
- **Consistency**: Use database triggers or application logic to sync

### 2. PostgreSQL Temporal Features
- Leverage PostgreSQL's native temporal capabilities
- Use `GENERATED ALWAYS AS` columns for computed fields
- Implement proper time-zone handling with `TIMESTAMPTZ`

## Core Temporal Tables

### 1. Animal Measurements (Weight & Physical Metrics)
```sql
CREATE TABLE animal_measurements (
    id BIGSERIAL PRIMARY KEY,
    animal_id BIGINT NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
    measurement_type VARCHAR(50) NOT NULL, -- 'weight', 'height', 'body_condition'
    value DECIMAL(10,2) NOT NULL,
    unit VARCHAR(10) NOT NULL, -- 'kg', 'lbs', 'cm'
    measured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    measured_by BIGINT REFERENCES users(id),
    method VARCHAR(50), -- 'scale', 'tape', 'visual_estimate'
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_animal_measurements_animal_type_time 
    ON animal_measurements(animal_id, measurement_type, measured_at DESC);
CREATE INDEX idx_animal_measurements_time 
    ON animal_measurements(measured_at DESC);
```

### 2. Health Records
```sql
CREATE TABLE animal_health_records (
    id BIGSERIAL PRIMARY KEY,
    animal_id BIGINT NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
    record_type VARCHAR(50) NOT NULL, -- 'vaccination', 'treatment', 'examination', 'illness'
    
    -- Vaccination specific
    vaccine_name VARCHAR(100),
    vaccine_batch VARCHAR(50),
    vaccination_date DATE,
    next_due_date DATE,
    
    -- Treatment specific
    treatment_name VARCHAR(100),
    diagnosis TEXT,
    treatment_start_date DATE,
    treatment_end_date DATE,
    medication TEXT,
    dosage VARCHAR(100),
    
    -- General health
    temperature DECIMAL(4,1),
    health_status VARCHAR(50), -- 'healthy', 'sick', 'injured', 'recovering'
    
    -- Common fields
    performed_by BIGINT REFERENCES users(id),
    veterinarian_name VARCHAR(100),
    cost DECIMAL(10,2),
    notes TEXT,
    attachments JSONB, -- Store file references
    
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_animal_health_records_animal_type_time 
    ON animal_health_records(animal_id, record_type, recorded_at DESC);
CREATE INDEX idx_animal_health_records_due_date 
    ON animal_health_records(next_due_date) WHERE next_due_date IS NOT NULL;
```

### 3. Location History
```sql
CREATE TABLE animal_locations (
    id BIGSERIAL PRIMARY KEY,
    animal_id BIGINT NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
    location_type VARCHAR(50) NOT NULL, -- 'pasture', 'barn', 'quarantine', 'hospital'
    location_name VARCHAR(100) NOT NULL,
    location_description TEXT,
    coordinates POINT, -- PostgreSQL geometric type for GPS coordinates
    
    moved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    moved_by BIGINT REFERENCES users(id),
    reason VARCHAR(100), -- 'grazing', 'breeding', 'treatment', 'quarantine'
    
    -- Auto-populated previous location
    previous_location_id BIGINT REFERENCES animal_locations(id),
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_animal_locations_animal_time 
    ON animal_locations(animal_id, moved_at DESC);
CREATE INDEX idx_animal_locations_current 
    ON animal_locations(animal_id, moved_at DESC) WHERE moved_at IS NOT NULL;
```

### 4. Breeding History
```sql
CREATE TABLE animal_breeding_events (
    id BIGSERIAL PRIMARY KEY,
    
    -- Primary animal (female for breeding, male for siring)
    animal_id BIGINT NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
    
    -- Partner information
    partner_id BIGINT REFERENCES animals(id),
    partner_external_info JSONB, -- For external/AI breeding
    
    -- Event details
    event_type VARCHAR(50) NOT NULL, -- 'breeding', 'ai_breeding', 'pregnancy_check', 'birth'
    event_date DATE NOT NULL,
    
    -- Breeding specific
    breeding_method VARCHAR(50), -- 'natural', 'artificial_insemination'
    breeding_success BOOLEAN,
    
    -- Pregnancy specific
    pregnancy_status VARCHAR(50), -- 'confirmed', 'suspected', 'failed'
    due_date DATE,
    gestation_period_days INTEGER,
    
    -- Birth specific
    birth_date DATE,
    offspring_count INTEGER DEFAULT 0,
    birth_weight DECIMAL(6,2),
    birth_complications TEXT,
    
    -- Financial
    cost DECIMAL(10,2),
    revenue DECIMAL(10,2),
    
    -- Metadata
    performed_by BIGINT REFERENCES users(id),
    veterinarian_name VARCHAR(100),
    notes TEXT,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_animal_breeding_events_animal_date 
    ON animal_breeding_events(animal_id, event_date DESC);
CREATE INDEX idx_animal_breeding_events_due_date 
    ON animal_breeding_events(due_date) WHERE due_date IS NOT NULL;
```

### 5. Financial Transactions
```sql
CREATE TABLE animal_financial_records (
    id BIGSERIAL PRIMARY KEY,
    animal_id BIGINT NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
    
    transaction_type VARCHAR(50) NOT NULL, -- 'purchase', 'sale', 'feed_cost', 'medical_cost', 'insurance'
    transaction_date DATE NOT NULL,
    
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    category VARCHAR(50), -- 'acquisition', 'maintenance', 'medical', 'breeding', 'disposal'
    
    -- Transaction details
    description TEXT,
    invoice_number VARCHAR(100),
    vendor_name VARCHAR(100),
    payment_method VARCHAR(50),
    
    -- References
    related_health_record_id BIGINT REFERENCES animal_health_records(id),
    related_breeding_event_id BIGINT REFERENCES animal_breeding_events(id),
    
    -- Metadata
    recorded_by BIGINT REFERENCES users(id),
    attachments JSONB,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_animal_financial_records_animal_date 
    ON animal_financial_records(animal_id, transaction_date DESC);
CREATE INDEX idx_animal_financial_records_type_date 
    ON animal_financial_records(transaction_type, transaction_date DESC);
```

### 6. Group Assignments History
```sql
CREATE TABLE animal_group_assignments (
    id BIGSERIAL PRIMARY KEY,
    animal_id BIGINT NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
    
    group_type VARCHAR(50) NOT NULL, -- 'herd', 'flock', 'breeding_group', 'treatment_group'
    group_name VARCHAR(100) NOT NULL,
    group_description TEXT,
    
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    assigned_by BIGINT REFERENCES users(id),
    removed_at TIMESTAMPTZ,
    removed_by BIGINT REFERENCES users(id),
    
    reason VARCHAR(100), -- 'age_grouping', 'breeding', 'treatment', 'feeding_schedule'
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_animal_group_assignments_animal_time 
    ON animal_group_assignments(animal_id, assigned_at DESC);
CREATE INDEX idx_animal_group_assignments_active 
    ON animal_group_assignments(animal_id, group_type) WHERE removed_at IS NULL;
```

## Enhanced Core Tables

### 1. Updated Animals Table (Current State)
```sql
-- Add computed columns for current state
ALTER TABLE animals 
ADD COLUMN current_weight DECIMAL(8,2) 
    GENERATED ALWAYS AS (
        (SELECT value FROM animal_measurements 
         WHERE animal_id = animals.id 
         AND measurement_type = 'weight' 
         ORDER BY measured_at DESC LIMIT 1)
    ) STORED;

ADD COLUMN current_location VARCHAR(100)
    GENERATED ALWAYS AS (
        (SELECT location_name FROM animal_locations 
         WHERE animal_id = animals.id 
         ORDER BY moved_at DESC LIMIT 1)
    ) STORED;

ADD COLUMN last_health_check_date DATE
    GENERATED ALWAYS AS (
        (SELECT recorded_at::date FROM animal_health_records 
         WHERE animal_id = animals.id 
         AND record_type = 'examination'
         ORDER BY recorded_at DESC LIMIT 1)
    ) STORED;
```

### 2. Lookup Tables
```sql
-- Vaccination types
CREATE TABLE vaccination_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    frequency_months INTEGER, -- Recommended frequency
    species_id BIGINT REFERENCES species(id),
    required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Location definitions
CREATE TABLE farm_locations (
    id SERIAL PRIMARY KEY,
    farm_id BIGINT NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    location_type VARCHAR(50) NOT NULL,
    description TEXT,
    coordinates POINT,
    capacity INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(farm_id, name)
);
```

## Performance Optimization

### 1. Partitioning Strategy
```sql
-- Partition large temporal tables by date
CREATE TABLE animal_measurements_2024 PARTITION OF animal_measurements
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE animal_measurements_2025 PARTITION OF animal_measurements
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

### 2. Materialized Views for Analytics
```sql
-- Animal summary view
CREATE MATERIALIZED VIEW animal_summary AS
SELECT 
    a.id,
    a.name,
    a.tag_number,
    s.name as species_name,
    b.name as breed_name,
    
    -- Latest measurements
    (SELECT value FROM animal_measurements am 
     WHERE am.animal_id = a.id AND am.measurement_type = 'weight' 
     ORDER BY measured_at DESC LIMIT 1) as current_weight,
    
    -- Health status
    (SELECT health_status FROM animal_health_records ahr 
     WHERE ahr.animal_id = a.id 
     ORDER BY recorded_at DESC LIMIT 1) as current_health_status,
    
    -- Location
    (SELECT location_name FROM animal_locations al 
     WHERE al.animal_id = a.id 
     ORDER BY moved_at DESC LIMIT 1) as current_location,
    
    -- Financial totals
    (SELECT SUM(amount) FROM animal_financial_records afr 
     WHERE afr.animal_id = a.id AND transaction_type LIKE '%cost%') as total_costs,
    
    (SELECT SUM(amount) FROM animal_financial_records afr 
     WHERE afr.animal_id = a.id AND transaction_type IN ('sale', 'milk_revenue')) as total_revenue

FROM animals a
LEFT JOIN species s ON a.species_id = s.id
LEFT JOIN breeds b ON a.breed_id = b.id
WHERE a.status = 'alive';

-- Refresh strategy
CREATE INDEX idx_animal_summary_refresh ON animal_summary(id);
```

## Data Integrity & Constraints

### 1. Check Constraints
```sql
-- Ensure logical data integrity
ALTER TABLE animal_measurements 
ADD CONSTRAINT chk_positive_value CHECK (value > 0);

ALTER TABLE animal_health_records 
ADD CONSTRAINT chk_valid_temperature CHECK (temperature BETWEEN 35.0 AND 45.0);

ALTER TABLE animal_breeding_events 
ADD CONSTRAINT chk_valid_gestation CHECK (gestation_period_days BETWEEN 20 AND 400);
```

### 2. Triggers for Data Consistency
```sql
-- Update animal current state when measurements change
CREATE OR REPLACE FUNCTION update_animal_current_state()
RETURNS TRIGGER AS $$
BEGIN
    -- Update current weight when new measurement is added
    IF NEW.measurement_type = 'weight' THEN
        UPDATE animals 
        SET weight = NEW.value, updated_at = NOW()
        WHERE id = NEW.animal_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_animal_current_state
    AFTER INSERT ON animal_measurements
    FOR EACH ROW
    EXECUTE FUNCTION update_animal_current_state();
```

## Migration Strategy

### 1. Data Migration Scripts
```sql
-- Migrate existing weight data
INSERT INTO animal_measurements (animal_id, measurement_type, value, unit, measured_at, notes)
SELECT 
    id, 
    'weight', 
    weight, 
    'kg', 
    COALESCE(updated_at, created_at),
    'Migrated from existing data'
FROM animals 
WHERE weight IS NOT NULL;

-- Migrate acquisition data to financial records
INSERT INTO animal_financial_records (animal_id, transaction_type, transaction_date, amount, description)
SELECT 
    id,
    'purchase',
    acquisition_date,
    0.00, -- Will need to be updated manually
    CONCAT('Animal acquired via ', acquisition_type)
FROM animals 
WHERE acquisition_type = 'purchased';
```

### 2. Gradual Migration Approach
1. **Phase 1**: Create new tables alongside existing ones
2. **Phase 2**: Implement dual-write to both old and new tables
3. **Phase 3**: Migrate existing data
4. **Phase 4**: Switch reads to new tables
5. **Phase 5**: Remove old columns after validation

This schema design provides a robust foundation for comprehensive animal tracking while maintaining compatibility with your existing Sequelize-based architecture.