'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		const [existing] = await queryInterface.sequelize.query(
			'SELECT id FROM breeds LIMIT 1;',
		);
		if (existing.length > 0) return;

		const now = new Date();

		// Look up species IDs by English name
		const [speciesRows] = await queryInterface.sequelize.query(
			`SELECT s.id, st.name
			 FROM species s
			 JOIN species_translation st ON st.species_id = s.id
			 WHERE st.language_code = 'en'
			 ORDER BY s.id ASC;`,
		);

		const speciesMap = {};
		for (const row of speciesRows) {
			speciesMap[row.name] = row.id;
		}

		const breedData = [
			{ species: 'Sheep', breeds: [{ en: 'Suffolk', es: 'Suffolk' }, { en: 'Merino', es: 'Merino' }, { en: 'Other', es: 'Otro' }] },
			{ species: 'Cattle', breeds: [{ en: 'Holstein', es: 'Holstein' }, { en: 'Angus', es: 'Angus' }, { en: 'Other', es: 'Otro' }] },
			{ species: 'Goat', breeds: [{ en: 'Boer', es: 'Boer' }, { en: 'Saanen', es: 'Saanen' }, { en: 'Other', es: 'Otro' }] },
			{ species: 'Pig', breeds: [{ en: 'Yorkshire', es: 'Yorkshire' }, { en: 'Duroc', es: 'Duroc' }, { en: 'Other', es: 'Otro' }] },
			{ species: 'Chicken', breeds: [{ en: 'Leghorn', es: 'Leghorn' }, { en: 'Rhode Island Red', es: 'Rhode Island Red' }, { en: 'Plymouth Rock', es: 'Plymouth Rock' }, { en: 'Other', es: 'Otro' }] },
		];

		for (const group of breedData) {
			const speciesId = speciesMap[group.species];

			// Insert breed rows for this species
			const breedRows = group.breeds.map(() => ({
				species_id: speciesId,
				created_at: now,
				updated_at: now,
			}));
			await queryInterface.bulkInsert('breeds', breedRows);

			// Query back the IDs we just inserted
			const [insertedBreeds] = await queryInterface.sequelize.query(
				`SELECT id FROM breeds
				 WHERE species_id = ${speciesId}
				 ORDER BY id ASC;`,
			);

			// Build translations using actual IDs
			const translations = [];
			for (let i = 0; i < group.breeds.length; i++) {
				const breedId = insertedBreeds[i].id;
				const breed = group.breeds[i];
				translations.push(
					{ breed_id: breedId, language_code: 'en', name: breed.en, created_at: now, updated_at: now },
					{ breed_id: breedId, language_code: 'es', name: breed.es, created_at: now, updated_at: now },
				);
			}
			await queryInterface.bulkInsert('breed_translation', translations);
		}
	},

	down: async (queryInterface, Sequelize) => {
		await queryInterface.bulkDelete('breed_translation', null, {});
		await queryInterface.bulkDelete('breeds', null, {});
	},
};
