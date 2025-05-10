"use strict";

/**
 * Migration to remove the name column from species and create species_translation table.
 * Follows project conventions: snake_case for DB fields, CommonJS syntax, timestamped filename.
 */

module.exports = {
	up: async (queryInterface, Sequelize) => {
		// Remove the name column from species
		await queryInterface.removeColumn("species", "name");

		// Create species_translation table
		await queryInterface.createTable("species_translation", {
			id: {
				type: Sequelize.INTEGER.UNSIGNED,
				autoIncrement: true,
				primaryKey: true,
				allowNull: false,
			},
			species_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: false,
				references: {
					model: "species",
					key: "id",
				},
				onDelete: "CASCADE",
			},
			language_code: {
				type: Sequelize.STRING(5),
				allowNull: false,
			},
			name: {
				type: Sequelize.STRING,
				allowNull: false,
			},
			created_at: {
				type: Sequelize.DATE,
				allowNull: false,
				defaultValue: Sequelize.literal("CURRENT_TIMESTAMP"),
			},
			updated_at: {
				type: Sequelize.DATE,
				allowNull: false,
				defaultValue: Sequelize.literal("CURRENT_TIMESTAMP"),
			},
		});
		// Add unique constraint for (species_id, language_code)
		await queryInterface.addConstraint("species_translation", {
			fields: ["species_id", "language_code"],
			type: "unique",
			name: "unique_species_language",
		});
	},

	down: async (queryInterface, Sequelize) => {
		// Drop species_translation table
		await queryInterface.dropTable("species_translation");
		// Add the name column back to species
		await queryInterface.addColumn("species", "name", {
			type: Sequelize.STRING,
			allowNull: false,
			unique: true,
		});
	},
};
