"use strict";

/**
 * Migration to add a unique constraint on (name, language_code) to species_translation table.
 * Follows project conventions: snake_case for DB fields, CommonJS syntax, timestamped filename.
 */

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.addConstraint("species_translation", {
			fields: ["name", "language_code"],
			type: "unique",
			name: "unique_species_translation_name_language",
		});
	},

	down: async (queryInterface, Sequelize) => {
		await queryInterface.removeConstraint("species_translation", "unique_species_translation_name_language");
	},
};
