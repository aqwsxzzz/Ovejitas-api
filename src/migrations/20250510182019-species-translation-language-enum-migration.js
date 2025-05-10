"use strict";

/**
 * Migration to change 'language_code' in 'species_translation' from STRING to ENUM('en', 'es').
 * Follows project conventions: CommonJS, kebab-case, timestamped filename, snake_case DB fields.
 */

module.exports = {
	up: async (queryInterface, Sequelize) => {
		// 1. Create ENUM type for language_code (if not exists)
		await queryInterface.changeColumn("species_translation", "language_code", {
			type: Sequelize.ENUM("en", "es"),
			allowNull: false,
		});
	},
	down: async (queryInterface, Sequelize) => {
		// 1. Revert ENUM back to STRING(5)
		await queryInterface.changeColumn("species_translation", "language_code", {
			type: Sequelize.STRING(5),
			allowNull: false,
		});
		// 2. Optionally drop the ENUM type if your DB supports it (e.g., Postgres)
		if (queryInterface.sequelize.getDialect() === "postgres") {
			await queryInterface.sequelize.query('DROP TYPE IF EXISTS "enum_species_translation_language_code";');
		}
	},
};
