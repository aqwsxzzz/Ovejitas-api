'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.addColumn('animals', 'group_name', {
			type: Sequelize.STRING,
			allowNull: true,
			field: 'group_name',
		});

		// Add index for group_name to improve query performance
		await queryInterface.addIndex('animals', ['group_name'], {
			name: 'idx_animals_group_name',
		});
	},

	down: async (queryInterface) => {
		await queryInterface.removeIndex('animals', 'idx_animals_group_name');
		await queryInterface.removeColumn('animals', 'group_name');
	},
};
