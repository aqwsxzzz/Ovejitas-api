"use strict";

module.exports = {
	up: async (queryInterface, Sequelize) => {
		const now = new Date();
		const breeds = [
			// sheep (species_id: 1)
			{ species_id: 1, name: "Suffolk", created_at: now, updated_at: now },
			{ species_id: 1, name: "Merino", created_at: now, updated_at: now },
			// cattle (species_id: 2)
			{ species_id: 2, name: "Holstein", created_at: now, updated_at: now },
			{ species_id: 2, name: "Angus", created_at: now, updated_at: now },
			// goat (species_id: 3)
			{ species_id: 3, name: "Boer", created_at: now, updated_at: now },
			{ species_id: 3, name: "Saanen", created_at: now, updated_at: now },
			// pig (species_id: 4)
			{ species_id: 4, name: "Yorkshire", created_at: now, updated_at: now },
			{ species_id: 4, name: "Duroc", created_at: now, updated_at: now },
		];
		await queryInterface.bulkInsert("breeds", breeds, {});
	},

	down: async (queryInterface, Sequelize) => {
		await queryInterface.bulkDelete(
			"breeds",
			{
				name: ["Suffolk", "Merino", "Holstein", "Angus", "Boer", "Saanen", "Yorkshire", "Duroc"],
			},
			{}
		);
	},
};
