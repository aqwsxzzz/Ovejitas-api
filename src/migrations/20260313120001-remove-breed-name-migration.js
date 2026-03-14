'use strict';

/**
 * Migration to remove the name column from breeds table.
 * Copies existing breed names into breed_translation (as 'en') before dropping the column.
 */

module.exports = {
	up: async (queryInterface, _Sequelize) => {
		// Copy existing breed names into breed_translation as English translations
		await queryInterface.sequelize.query(`
			INSERT INTO breed_translation (breed_id, language_code, name, created_at, updated_at)
			SELECT id, 'en', name, created_at, updated_at
			FROM breeds
			WHERE name IS NOT NULL AND name != ''
		`);

		// Remove the unique constraint on (species_id, name)
		await queryInterface.removeIndex('breeds', ['species_id', 'name']);

		// Remove the name column
		await queryInterface.removeColumn('breeds', 'name');
	},

	down: async (queryInterface, Sequelize) => {
		// Re-add the name column
		await queryInterface.addColumn('breeds', 'name', {
			type: Sequelize.STRING,
			allowNull: false,
			defaultValue: '',
		});

		// Restore names from English translations
		await queryInterface.sequelize.query(`
			UPDATE breeds
			SET name = bt.name
			FROM breed_translation bt
			WHERE bt.breed_id = breeds.id AND bt.language_code = 'en'
		`);

		// Re-add the unique constraint
		await queryInterface.addIndex('breeds', ['species_id', 'name'], {
			unique: true,
			name: 'breeds_species_id_name',
		});

		// Remove the migrated translations
		await queryInterface.sequelize.query(`
			DELETE FROM breed_translation
		`);
	},
};
