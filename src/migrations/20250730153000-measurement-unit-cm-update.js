'use strict';

module.exports = {
	up: async (queryInterface) => {
		// First update the enum type to replace 'cms' with 'cm'
		await queryInterface.sequelize.query(`
      ALTER TYPE "enum_animal_measurements_unit" RENAME TO "enum_animal_measurements_unit_old";
    `);

		await queryInterface.sequelize.query(`
      CREATE TYPE "enum_animal_measurements_unit" AS ENUM('kg', 'cm', 'celsius');
    `);

		// Update the column to use the new enum, converting 'cms' to 'cm'
		await queryInterface.sequelize.query(`
      ALTER TABLE animal_measurements 
      ALTER COLUMN unit TYPE "enum_animal_measurements_unit" 
      USING (
        CASE 
          WHEN unit = 'cms' THEN 'cm'::"enum_animal_measurements_unit"
          ELSE unit::text::"enum_animal_measurements_unit"
        END
      );
    `);

		// Drop the old enum type
		await queryInterface.sequelize.query(`
      DROP TYPE "enum_animal_measurements_unit_old";
    `);
	},

	down: async (queryInterface) => {
		// Reverse the process - rename current enum to old
		await queryInterface.sequelize.query(`
      ALTER TYPE "enum_animal_measurements_unit" RENAME TO "enum_animal_measurements_unit_old";
    `);

		// Create the original enum with 'cms'
		await queryInterface.sequelize.query(`
      CREATE TYPE "enum_animal_measurements_unit" AS ENUM('kg', 'cms', 'celsius');
    `);

		// Update the column back to original enum, converting 'cm' to 'cms'
		await queryInterface.sequelize.query(`
      ALTER TABLE animal_measurements 
      ALTER COLUMN unit TYPE "enum_animal_measurements_unit" 
      USING (
        CASE 
          WHEN unit = 'cm' THEN 'cms'::"enum_animal_measurements_unit"
          ELSE unit::text::"enum_animal_measurements_unit"
        END
      );
    `);

		// Drop the temporary enum type
		await queryInterface.sequelize.query(`
      DROP TYPE "enum_animal_measurements_unit_old";
    `);
	},
};
