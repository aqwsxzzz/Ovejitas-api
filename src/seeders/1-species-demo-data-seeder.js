'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		// Check for our specific seeded species — not "any species" — because the
		// chicken species is inserted by an earlier migration, and a blanket
		// existence check would skip the rest of our seed data.
		const [existing] = await queryInterface.sequelize.query(
			`SELECT s.id FROM species s
			 JOIN species_translation st ON st.species_id = s.id
			 WHERE st.language_code = 'en' AND st.name = 'Sheep'`,
		);
		if (existing.length > 0) return;

		const now = new Date();

		// Chicken is created by an earlier migration, so only insert the other
		// four species here. Capture ids directly from RETURNING to avoid
		// colliding with the pre-existing chicken row when ordering by id.
		const [insertedRows] = await queryInterface.sequelize.query(
			`INSERT INTO species (created_at, updated_at)
			 VALUES (:now, :now), (:now, :now), (:now, :now), (:now, :now)
			 RETURNING id`,
			{ replacements: { now } },
		);
		const [sheepId, cattleId, goatId, pigId] = insertedRows.map((r) => r.id);

		const speciesTranslations = [
			{ species_id: sheepId, language_code: 'en', name: 'Sheep', created_at: now, updated_at: now },
			{ species_id: sheepId, language_code: 'es', name: 'Ovino', created_at: now, updated_at: now },
			{ species_id: cattleId, language_code: 'en', name: 'Cattle', created_at: now, updated_at: now },
			{ species_id: cattleId, language_code: 'es', name: 'Bovino', created_at: now, updated_at: now },
			{ species_id: goatId, language_code: 'en', name: 'Goat', created_at: now, updated_at: now },
			{ species_id: goatId, language_code: 'es', name: 'Caprino', created_at: now, updated_at: now },
			{ species_id: pigId, language_code: 'en', name: 'Pig', created_at: now, updated_at: now },
			{ species_id: pigId, language_code: 'es', name: 'Porcino', created_at: now, updated_at: now },
		];
		await queryInterface.bulkInsert('species_translation', speciesTranslations);
	},

	down: async (queryInterface, Sequelize) => {
		await queryInterface.bulkDelete('species_translation', null, {});
		await queryInterface.bulkDelete('species', null, {});
	},
};
