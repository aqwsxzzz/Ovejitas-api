"use strict";

/**
 * Migration to add a unique constraint on (species_id, name) to species_translation table.
 * Follows project conventions: snake_case for DB fields, CommonJS syntax, timestamped filename.
 */

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.addConstraint("species_translation", {
			fields: ["species_id", "name"],
			type: "unique",
			name: "unique_species_name_per_species",
		});
	},

	down: async (queryInterface, Sequelize) => {
		await queryInterface.removeConstraint("species_translation", "unique_species_name_per_species");
	},
};
