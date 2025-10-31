'use strict';

/**
 * Migration for creating the species table.
 * Follows project conventions: snake_case for DB fields, CommonJS syntax, timestamped filename.
 */

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.createTable('species', {
			id: {
				type: Sequelize.INTEGER.UNSIGNED,
				autoIncrement: true,
				primaryKey: true,
				allowNull: false,
			},

			created_at: {
				type: Sequelize.DATE,
				allowNull: false,
				defaultValue: Sequelize.literal('CURRENT_TIMESTAMP'),
			},
			updated_at: {
				type: Sequelize.DATE,
				allowNull: false,
				defaultValue: Sequelize.literal('CURRENT_TIMESTAMP'),
			},
		});
	},

	down: async (queryInterface) => {
		await queryInterface.dropTable('species');
	},
};
