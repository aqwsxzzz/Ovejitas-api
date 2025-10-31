'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		// Insert species (base table)
		const now = new Date();
		const species = [
			{ created_at: now, updated_at: now }, // sheep
			{ created_at: now, updated_at: now }, // cattle
			{ created_at: now, updated_at: now }, // goat
			{ created_at: now, updated_at: now }, // pig
		];
		await queryInterface.bulkInsert('species', species, {});

		// Get inserted species IDs (assuming auto-increment starts at 1 and order is preserved)
		// If not, you may need to query for them by other means.
		const speciesTranslations = [
			// sheep
			{ species_id: 1, language_code: 'en', name: 'Sheep', created_at: now, updated_at: now },
			{ species_id: 1, language_code: 'es', name: 'Ovino', created_at: now, updated_at: now },
			// cattle
			{ species_id: 2, language_code: 'en', name: 'Cattle', created_at: now, updated_at: now },
			{ species_id: 2, language_code: 'es', name: 'Bovino', created_at: now, updated_at: now },
			// goat
			{ species_id: 3, language_code: 'en', name: 'Goat', created_at: now, updated_at: now },
			{ species_id: 3, language_code: 'es', name: 'Caprino', created_at: now, updated_at: now },
			// pig
			{ species_id: 4, language_code: 'en', name: 'Pig', created_at: now, updated_at: now },
			{ species_id: 4, language_code: 'es', name: 'Porcino', created_at: now, updated_at: now },
		];
		await queryInterface.bulkInsert('species_translation', speciesTranslations, {});
	},

	down: async (queryInterface, Sequelize) => {
		// Remove all seeded translations and species
		await queryInterface.bulkDelete(
			'species_translation',
			{
				name: ['sheep', 'Ovino', 'cattle', 'Bovino', 'goat', 'Caprino', 'pig', 'Porcino'],
			},
			{},
		);
		await queryInterface.bulkDelete('species', null, {});
	},
};
