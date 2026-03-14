'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		const [existing] = await queryInterface.sequelize.query(
			'SELECT id FROM species LIMIT 1;',
		);
		if (existing.length > 0) return;

		const now = new Date();

		await queryInterface.bulkInsert('species', [
			{ created_at: now, updated_at: now },
			{ created_at: now, updated_at: now },
			{ created_at: now, updated_at: now },
			{ created_at: now, updated_at: now },
		]);

		const [rows] = await queryInterface.sequelize.query(
			'SELECT id FROM species ORDER BY id ASC;',
		);
		const [sheepId, cattleId, goatId, pigId] = rows.map((r) => r.id);

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
