"use strict";

module.exports = {
	up: async (queryInterface, Sequelize) => {
		// Remove old constraint
		await queryInterface.removeConstraint("animals", "unique_farm_tag_number");
		// Add new constraint
		await queryInterface.addConstraint("animals", {
			fields: ["farm_id", "species_id", "tag_number"],
			type: "unique",
			name: "unique_farm_species_tag_number",
			where: {
				tag_number: { [Sequelize.Op.ne]: null },
			},
		});
	},

	down: async (queryInterface, Sequelize) => {
		// Remove new constraint
		await queryInterface.removeConstraint("animals", "unique_farm_species_tag_number");
		// Restore old constraint
		await queryInterface.addConstraint("animals", {
			fields: ["farm_id", "tag_number"],
			type: "unique",
			name: "unique_farm_tag_number",
			where: {
				tag_number: { [Sequelize.Op.ne]: null },
			},
		});
	},
};
