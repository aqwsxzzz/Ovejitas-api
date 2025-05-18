"use strict";

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.createTable("breeds", {
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
			name: {
				type: Sequelize.STRING,
				allowNull: false,
			},
			created_at: {
				type: Sequelize.DATE,
				allowNull: false,
				defaultValue: Sequelize.fn("NOW"),
			},
			updated_at: {
				type: Sequelize.DATE,
				allowNull: false,
				defaultValue: Sequelize.fn("NOW"),
			},
		});
		await queryInterface.addConstraint("breeds", {
			fields: ["species_id", "name"],
			type: "unique",
			name: "unique_species_breed_name",
		});
	},
	down: async (queryInterface) => {
		await queryInterface.dropTable("breeds");
	},
};
