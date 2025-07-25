'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		// Check if weight_id column already exists
		const [results] = await queryInterface.sequelize.query(`
			SELECT column_name 
			FROM information_schema.columns 
			WHERE table_name = 'animals' AND column_name = 'weight_id';
		`);

		if (results.length === 0) {
			// Add weight_id column to animals table
			await queryInterface.addColumn('animals', 'weight_id', {
				type: Sequelize.INTEGER,
				allowNull: true,
				field: 'weight_id',
				references: { model: 'animal_measurements', key: 'id' },
				onDelete: 'SET NULL',
			});
		}

		// Add default values to animal enums
		await queryInterface.changeColumn('animals', 'sex', {
			type: Sequelize.ENUM('male', 'female', 'unknown'),
			allowNull: false,
			defaultValue: 'unknown',
		});

		await queryInterface.changeColumn('animals', 'status', {
			type: Sequelize.ENUM('alive', 'sold', 'deceased'),
			allowNull: false,
			defaultValue: 'alive',
		});

		await queryInterface.changeColumn('animals', 'reproductive_status', {
			type: Sequelize.ENUM('open', 'pregnant', 'lactating', 'other'),
			allowNull: false,
			defaultValue: 'other',
		});

		await queryInterface.changeColumn('animals', 'acquisition_type', {
			type: Sequelize.ENUM('born', 'purchased', 'other'),
			allowNull: false,
			defaultValue: 'other',
		});

		// Update animal_measurements table
		// Change id from BIGINT to INTEGER
		// First drop the foreign key that references this primary key
		await queryInterface.sequelize.query(`
			ALTER TABLE animals DROP CONSTRAINT IF EXISTS animals_weight_id_fkey;
		`);

		// Drop the primary key constraint
		await queryInterface.sequelize.query(`
			ALTER TABLE animal_measurements DROP CONSTRAINT animal_measurements_pkey;
		`);

		// Change the column type
		await queryInterface.sequelize.query(`
			ALTER TABLE animal_measurements ALTER COLUMN id TYPE INTEGER USING id::INTEGER;
		`);

		// Re-add the primary key constraint
		await queryInterface.sequelize.query(`
			ALTER TABLE animal_measurements ADD CONSTRAINT animal_measurements_pkey PRIMARY KEY (id);
		`);

		// Re-add the foreign key constraint (will be added later with weight_id column if needed)
		const [weightIdResults] = await queryInterface.sequelize.query(`
			SELECT column_name 
			FROM information_schema.columns 
			WHERE table_name = 'animals' AND column_name = 'weight_id';
		`);

		if (weightIdResults.length > 0) {
			await queryInterface.sequelize.query(`
				ALTER TABLE animals ADD CONSTRAINT animals_weight_id_fkey 
				FOREIGN KEY (weight_id) REFERENCES animal_measurements(id) ON DELETE SET NULL;
			`);
		}

		// Change animal_id from BIGINT to INTEGER.UNSIGNED
		await queryInterface.changeColumn('animal_measurements', 'animal_id', {
			type: Sequelize.INTEGER.UNSIGNED,
			allowNull: false,
			references: {
				model: 'animals',
				key: 'id',
			},
		});

		// Change measured_by from BIGINT to INTEGER
		await queryInterface.changeColumn('animal_measurements', 'measured_by', {
			type: Sequelize.INTEGER,
			allowNull: true,
			references: {
				model: 'users',
				key: 'id',
			},
		});

		// Update measurement_type enum to replace body_condition with temperature
		// First update any existing body_condition records to weight (or handle as needed)
		await queryInterface.sequelize.query(`
      UPDATE animal_measurements 
      SET measurement_type = 'weight'
      WHERE measurement_type = 'body_condition';
    `);

		// Create new enum type without body_condition but with temperature
		await queryInterface.sequelize.query(`
      CREATE TYPE "enum_animal_measurements_measurement_type_new" AS ENUM('weight', 'height', 'temperature');
    `);

		// Change column to use new enum
		await queryInterface.sequelize.query(`
      ALTER TABLE animal_measurements 
      ALTER COLUMN measurement_type TYPE "enum_animal_measurements_measurement_type_new" 
      USING measurement_type::text::"enum_animal_measurements_measurement_type_new";
    `);

		// Drop old enum type
		await queryInterface.sequelize.query(`
      DROP TYPE "enum_animal_measurements_measurement_type";
    `);

		// Rename new enum to original name
		await queryInterface.sequelize.query(`
      ALTER TYPE "enum_animal_measurements_measurement_type_new" RENAME TO "enum_animal_measurements_measurement_type";
    `);

		// Convert unit column to ENUM
		// First, update existing values to match enum values
		await queryInterface.sequelize.query(`
      UPDATE animal_measurements 
      SET unit = LOWER(unit)
      WHERE unit IS NOT NULL;
    `);

		// Update specific values to match enum
		await queryInterface.sequelize.query(`
      UPDATE animal_measurements 
      SET unit = 'kg' 
      WHERE measurement_type = 'weight' AND unit NOT IN ('kg', 'cms', 'celsius');
    `);

		await queryInterface.sequelize.query(`
      UPDATE animal_measurements 
      SET unit = 'cms' 
      WHERE measurement_type = 'height' AND unit NOT IN ('kg', 'cms', 'celsius');
    `);

		await queryInterface.sequelize.query(`
      UPDATE animal_measurements 
      SET unit = 'celsius' 
      WHERE measurement_type = 'temperature' AND unit NOT IN ('kg', 'cms', 'celsius');
    `);

		// Create enum type for unit
		await queryInterface.sequelize.query(`
      CREATE TYPE "enum_animal_measurements_unit" AS ENUM('kg', 'cms', 'celsius');
    `);

		// Change unit column to use enum
		await queryInterface.sequelize.query(`
      ALTER TABLE animal_measurements 
      ALTER COLUMN unit TYPE "enum_animal_measurements_unit" 
      USING unit::"enum_animal_measurements_unit";
    `);

		// Remove method column
		await queryInterface.removeColumn('animal_measurements', 'method');

		// Check if weight column exists before removing it
		const [weightExists] = await queryInterface.sequelize.query(`
			SELECT column_name 
			FROM information_schema.columns 
			WHERE table_name = 'animals' AND column_name = 'weight';
		`);

		if (weightExists.length > 0) {
			// After all animal_measurements changes, remove weight column from animals
			await queryInterface.removeColumn('animals', 'weight');
		}
	},

	down: async (queryInterface, Sequelize) => {
		// Add weight column back to animals
		await queryInterface.addColumn('animals', 'weight', {
			type: Sequelize.FLOAT,
			allowNull: true,
			field: 'weight',
		});

		// Remove weight_id column from animals
		await queryInterface.removeColumn('animals', 'weight_id');

		// Remove default values from animal enums
		await queryInterface.changeColumn('animals', 'sex', {
			type: Sequelize.ENUM('male', 'female', 'unknown'),
			allowNull: false,
		});

		await queryInterface.changeColumn('animals', 'status', {
			type: Sequelize.ENUM('alive', 'sold', 'deceased'),
			allowNull: false,
		});

		await queryInterface.changeColumn('animals', 'reproductive_status', {
			type: Sequelize.ENUM('open', 'pregnant', 'lactating', 'other'),
			allowNull: false,
		});

		await queryInterface.changeColumn('animals', 'acquisition_type', {
			type: Sequelize.ENUM('born', 'purchased', 'other'),
			allowNull: false,
		});

		// Revert animal_measurements changes
		// Add method column back
		await queryInterface.addColumn('animal_measurements', 'method', {
			type: Sequelize.STRING(50),
			allowNull: true,
		});

		// Change unit back to STRING
		await queryInterface.changeColumn('animal_measurements', 'unit', {
			type: Sequelize.STRING(10),
			allowNull: false,
		});

		// Drop unit enum type
		await queryInterface.sequelize.query(`
      DROP TYPE "enum_animal_measurements_unit";
    `);

		// Revert measurement_type enum to include body_condition
		await queryInterface.sequelize.query(`
      CREATE TYPE "enum_animal_measurements_measurement_type_new" AS ENUM('weight', 'height', 'body_condition');
    `);

		await queryInterface.sequelize.query(`
      ALTER TABLE animal_measurements 
      ALTER COLUMN measurement_type TYPE "enum_animal_measurements_measurement_type_new" 
      USING measurement_type::text::"enum_animal_measurements_measurement_type_new";
    `);

		await queryInterface.sequelize.query(`
      DROP TYPE "enum_animal_measurements_measurement_type";
    `);

		await queryInterface.sequelize.query(`
      ALTER TYPE "enum_animal_measurements_measurement_type_new" RENAME TO "enum_animal_measurements_measurement_type";
    `);

		// Revert measured_by to BIGINT
		await queryInterface.changeColumn('animal_measurements', 'measured_by', {
			type: Sequelize.BIGINT,
			allowNull: true,
			references: {
				model: 'users',
				key: 'id',
			},
		});

		// Revert animal_id to BIGINT
		await queryInterface.changeColumn('animal_measurements', 'animal_id', {
			type: Sequelize.BIGINT,
			allowNull: false,
			references: {
				model: 'animals',
				key: 'id',
			},
		});

		// Revert id to BIGINT
		// First drop the primary key constraint
		await queryInterface.sequelize.query(`
			ALTER TABLE animal_measurements DROP CONSTRAINT animal_measurements_pkey;
		`);

		// Change the column type back to BIGINT
		await queryInterface.sequelize.query(`
			ALTER TABLE animal_measurements ALTER COLUMN id TYPE BIGINT USING id::BIGINT;
		`);

		// Re-add the primary key constraint
		await queryInterface.sequelize.query(`
			ALTER TABLE animal_measurements ADD CONSTRAINT animal_measurements_pkey PRIMARY KEY (id);
		`);
	},
};
