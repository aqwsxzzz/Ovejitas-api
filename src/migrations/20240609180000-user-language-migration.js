"use strict";

/**
 * Add 'language' column to 'users' table as ENUM('en', 'es'), not nullable, default 'es'.
 */

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.addColumn("users", "language", {
			type: Sequelize.ENUM("en", "es"),
			allowNull: false,
			defaultValue: "en",
		});
	},

	down: async (queryInterface, Sequelize) => {
		await queryInterface.removeColumn("users", "language");
		// Optionally drop the ENUM type if your DB supports it (e.g., Postgres)
		if (queryInterface.sequelize.getDialect() === "postgres") {
			await queryInterface.sequelize.query('DROP TYPE IF EXISTS "enum_users_language";');
		}
	},
};
