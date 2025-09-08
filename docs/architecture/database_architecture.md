# Database Architecture

PostgreSQL + Sequelize ORM for livestock management with multi-tenant farm isolation.

```
users                # Auth & user management
├─ farms             # Farm isolation (multi-tenant)
├─ farm_members      # User ↔ Farm relationships (owner/member)  
├─ farm_invitations  # Invitation system

species              # Animal species (cattle, sheep, etc)
├─ species_translation  # I18n support (en/es)
├─ breeds            # Breed catalog per species

animals              # Core livestock entity
├─ animal_measurements  # Time-series data (weight, height)

expenses             # Farm expense tracking
                     # Links to animals/species/breeds (optional)

Key relationships:
- Users belong to multiple farms via farm_members
- Animals scoped to farms with unique tag_numbers + group_name
- Parent tracking (father_id/mother_id for genealogy)
- Latest weight cached for performance
- Expenses optionally linked to specific animals/species/breeds
```

## Key Design Patterns

**Multi-tenant**: Farm-scoped data isolation  
**I18n**: Species translations for en/es support  
**Temporal**: Time-series measurements tracking  
**Genealogy**: Self-referential animal parent relationships  
**Security**: Hashids for public ID obfuscation

## Critical Constraints

- **Unique animal tags**: `(farm_id, species_id, tag_number)`
- **Unique breeds**: `(species_id, name)`
- **Farm isolation**: All data scoped by `farm_id` (animals, expenses)
- **Performance indexes**: Expenses by farm+date, measurements by animal+type+time

## Migration Files

Located in `/src/migrations/` with timestamp ordering. Run `npm run migrate` for development setup.