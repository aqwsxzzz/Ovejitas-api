'use strict';

/** @type {import('sequelize-cli').Migration} */
module.exports = {
	async up(queryInterface) {
		// Create function to sync weight to animals table
		await queryInterface.sequelize.query(`
      CREATE OR REPLACE FUNCTION sync_animal_weight()
      RETURNS TRIGGER AS $$
      BEGIN
        -- Only sync if this is a weight measurement
        IF NEW.measurement_type = 'weight' THEN
          -- Update the animal's weight with the latest weight measurement
          UPDATE animals 
          SET weight = NEW.value, 
              updated_at = NOW()
          WHERE id = NEW.animal_id;
        END IF;
        
        RETURN NEW;
      END;
      $$ LANGUAGE plpgsql;
    `);

		// Create trigger that fires after insert on animal_measurements
		await queryInterface.sequelize.query(`
      CREATE TRIGGER trigger_sync_animal_weight
      AFTER INSERT ON animal_measurements
      FOR EACH ROW
      EXECUTE FUNCTION sync_animal_weight();
    `);

		// Create trigger that fires after update on animal_measurements
		await queryInterface.sequelize.query(`
      CREATE TRIGGER trigger_sync_animal_weight_update
      AFTER UPDATE ON animal_measurements
      FOR EACH ROW
      EXECUTE FUNCTION sync_animal_weight();
    `);
	},

	async down(queryInterface) {
		// Drop triggers
		await queryInterface.sequelize.query(`
      DROP TRIGGER IF EXISTS trigger_sync_animal_weight ON animal_measurements;
    `);

		await queryInterface.sequelize.query(`
      DROP TRIGGER IF EXISTS trigger_sync_animal_weight_update ON animal_measurements;
    `);

		// Drop function
		await queryInterface.sequelize.query(`
      DROP FUNCTION IF EXISTS sync_animal_weight();
    `);
	},
};
