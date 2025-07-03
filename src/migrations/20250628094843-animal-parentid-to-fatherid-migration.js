"use strict";

module.exports = {
	up: async (queryInterface, Sequelize) => {
		// Rename column parent_id to father_id
		await queryInterface.renameColumn("animals", "parent_id", "father_id");
		// If there are any constraints or indexes involving parent_id, update them here if needed
	},

	down: async (queryInterface, Sequelize) => {
		// Revert column name from father_id back to parent_id
		await queryInterface.renameColumn("animals", "father_id", "parent_id");
		// Revert any constraints or indexes if changed above
	},
};
