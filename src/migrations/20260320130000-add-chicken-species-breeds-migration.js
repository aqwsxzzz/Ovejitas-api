'use strict';

module.exports = {
	up: async (queryInterface) => {
		const now = new Date();

		// Check if Chicken species already exists
		const [existing] = await queryInterface.sequelize.query(
			`SELECT s.id FROM species s
			 JOIN species_translation st ON st.species_id = s.id
			 WHERE st.language_code = 'en' AND st.name = 'Chicken'`,
		);
		if (existing.length > 0) return;

		// Create species row
		const [speciesRows] = await queryInterface.sequelize.query(
			`INSERT INTO species (created_at, updated_at)
			 VALUES (:now, :now)
			 RETURNING id`,
			{ replacements: { now } },
		);
		const chickenId = speciesRows[0].id;

		// Species translations
		await queryInterface.bulkInsert('species_translation', [
			{ species_id: chickenId, language_code: 'en', name: 'Chicken', created_at: now, updated_at: now },
			{ species_id: chickenId, language_code: 'es', name: 'Pollo', created_at: now, updated_at: now },
		]);

		// Breeds
		const breedData = [
			{ en: 'Leghorn', es: 'Leghorn' },
			{ en: 'Rhode Island Red', es: 'Rhode Island Red' },
			{ en: 'Plymouth Rock', es: 'Plymouth Rock' },
			{ en: 'Other', es: 'Otro' },
		];

		for (const breed of breedData) {
			const [breedRows] = await queryInterface.sequelize.query(
				`INSERT INTO breeds (species_id, created_at, updated_at)
				 VALUES (:chickenId, :now, :now)
				 RETURNING id`,
				{ replacements: { chickenId, now } },
			);
			const breedId = breedRows[0].id;

			await queryInterface.bulkInsert('breed_translation', [
				{ breed_id: breedId, language_code: 'en', name: breed.en, created_at: now, updated_at: now },
				{ breed_id: breedId, language_code: 'es', name: breed.es, created_at: now, updated_at: now },
			]);
		}
	},

	down: async (queryInterface) => {
		// Find the chicken species ID
		const [rows] = await queryInterface.sequelize.query(
			`SELECT s.id FROM species s
			 JOIN species_translation st ON st.species_id = s.id
			 WHERE st.language_code = 'en' AND st.name = 'Chicken'`,
		);
		if (rows.length === 0) return;

		const chickenId = rows[0].id;

		// Cascade: breed_translation → breeds → species_translation → species
		await queryInterface.sequelize.query(
			`DELETE FROM breed_translation WHERE breed_id IN (SELECT id FROM breeds WHERE species_id = :chickenId)`,
			{ replacements: { chickenId } },
		);
		await queryInterface.sequelize.query(
			`DELETE FROM breeds WHERE species_id = :chickenId`,
			{ replacements: { chickenId } },
		);
		await queryInterface.sequelize.query(
			`DELETE FROM species_translation WHERE species_id = :chickenId`,
			{ replacements: { chickenId } },
		);
		await queryInterface.sequelize.query(
			`DELETE FROM species WHERE id = :chickenId`,
			{ replacements: { chickenId } },
		);
	},
};
