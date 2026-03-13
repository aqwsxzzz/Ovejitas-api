"use strict";

module.exports = {
	up: async (queryInterface, Sequelize) => {
		const now = new Date();

		// Insert breeds (base table, no name)
		const breeds = [
			// sheep (species_id: 1)
			{ species_id: 1, created_at: now, updated_at: now },
			{ species_id: 1, created_at: now, updated_at: now },
			{ species_id: 1, created_at: now, updated_at: now },
			// cattle (species_id: 2)
			{ species_id: 2, created_at: now, updated_at: now },
			{ species_id: 2, created_at: now, updated_at: now },
			{ species_id: 2, created_at: now, updated_at: now },
			// goat (species_id: 3)
			{ species_id: 3, created_at: now, updated_at: now },
			{ species_id: 3, created_at: now, updated_at: now },
			{ species_id: 3, created_at: now, updated_at: now },
			// pig (species_id: 4)
			{ species_id: 4, created_at: now, updated_at: now },
			{ species_id: 4, created_at: now, updated_at: now },
			{ species_id: 4, created_at: now, updated_at: now },
		];
		await queryInterface.bulkInsert("breeds", breeds, {});

		// Insert breed translations (en + es)
		const breedTranslations = [
			// sheep breeds (breed_id: 1-3)
			{ breed_id: 1, language_code: "en", name: "Suffolk", created_at: now, updated_at: now },
			{ breed_id: 1, language_code: "es", name: "Suffolk", created_at: now, updated_at: now },
			{ breed_id: 2, language_code: "en", name: "Merino", created_at: now, updated_at: now },
			{ breed_id: 2, language_code: "es", name: "Merino", created_at: now, updated_at: now },
			{ breed_id: 3, language_code: "en", name: "Other", created_at: now, updated_at: now },
			{ breed_id: 3, language_code: "es", name: "Otro", created_at: now, updated_at: now },
			// cattle breeds (breed_id: 4-6)
			{ breed_id: 4, language_code: "en", name: "Holstein", created_at: now, updated_at: now },
			{ breed_id: 4, language_code: "es", name: "Holstein", created_at: now, updated_at: now },
			{ breed_id: 5, language_code: "en", name: "Angus", created_at: now, updated_at: now },
			{ breed_id: 5, language_code: "es", name: "Angus", created_at: now, updated_at: now },
			{ breed_id: 6, language_code: "en", name: "Other", created_at: now, updated_at: now },
			{ breed_id: 6, language_code: "es", name: "Otro", created_at: now, updated_at: now },
			// goat breeds (breed_id: 7-9)
			{ breed_id: 7, language_code: "en", name: "Boer", created_at: now, updated_at: now },
			{ breed_id: 7, language_code: "es", name: "Boer", created_at: now, updated_at: now },
			{ breed_id: 8, language_code: "en", name: "Saanen", created_at: now, updated_at: now },
			{ breed_id: 8, language_code: "es", name: "Saanen", created_at: now, updated_at: now },
			{ breed_id: 9, language_code: "en", name: "Other", created_at: now, updated_at: now },
			{ breed_id: 9, language_code: "es", name: "Otro", created_at: now, updated_at: now },
			// pig breeds (breed_id: 10-12)
			{ breed_id: 10, language_code: "en", name: "Yorkshire", created_at: now, updated_at: now },
			{ breed_id: 10, language_code: "es", name: "Yorkshire", created_at: now, updated_at: now },
			{ breed_id: 11, language_code: "en", name: "Duroc", created_at: now, updated_at: now },
			{ breed_id: 11, language_code: "es", name: "Duroc", created_at: now, updated_at: now },
			{ breed_id: 12, language_code: "en", name: "Other", created_at: now, updated_at: now },
			{ breed_id: 12, language_code: "es", name: "Otro", created_at: now, updated_at: now },
		];
		await queryInterface.bulkInsert("breed_translation", breedTranslations, {});
	},

	down: async (queryInterface, Sequelize) => {
		await queryInterface.bulkDelete("breed_translation", null, {});
		await queryInterface.bulkDelete("breeds", null, {});
	},
};
