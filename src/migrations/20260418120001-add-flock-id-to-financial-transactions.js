'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.addColumn('financial_transactions', 'flock_id', {
			type: Sequelize.INTEGER.UNSIGNED,
			allowNull: true,
			references: { model: 'flocks', key: 'id' },
			onUpdate: 'CASCADE',
			onDelete: 'SET NULL',
		});

		await queryInterface.addIndex('financial_transactions', ['flock_id'], {
			name: 'idx_financial_transactions_flock',
		});
	},

	down: async (queryInterface) => {
		await queryInterface.removeIndex('financial_transactions', 'idx_financial_transactions_flock');
		await queryInterface.removeColumn('financial_transactions', 'flock_id');
	},
};
