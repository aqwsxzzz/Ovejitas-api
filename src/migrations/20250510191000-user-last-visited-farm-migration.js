"use strict";

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.addColumn("users", "last_visited_farm_id", {
			type: Sequelize.INTEGER.UNSIGNED,
			allowNull: true,
		});
	},

	down: async (queryInterface) => {
		await queryInterface.removeColumn("users", "last_visited_farm_id");
	},
};
