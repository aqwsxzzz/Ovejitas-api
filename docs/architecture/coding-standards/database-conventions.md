# Database Conventions

- Tables: `snake_case` plural (`expenses`, `animal_measurements`)
- Columns: `snake_case` with field mapping (`farmId` → `farm_id`)
- Foreign keys: `{table_singular}_id` (`farm_id`, `animal_id`)
- Indexes: `idx_{table}_{columns}`