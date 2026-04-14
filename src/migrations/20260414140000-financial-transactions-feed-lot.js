'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		// 1. Allow species_id to be null — feed purchases span species (farm-wide expense).
		// Use raw SQL: Sequelize's changeColumn on Postgres can leave duplicate FK constraints.
		await queryInterface.sequelize.query(
			'ALTER TABLE financial_transactions ALTER COLUMN species_id DROP NOT NULL',
		);

		// 2. Add back-reference to feed_lots so a lot purchase can be linked to its ledger entry.
		// SET NULL on lot delete keeps the historical expense even if an unused lot is deleted.
		await queryInterface.addColumn('financial_transactions', 'feed_lot_id', {
			type: Sequelize.INTEGER.UNSIGNED,
			allowNull: true,
			references: { model: 'feed_lots', key: 'id' },
			onUpdate: 'CASCADE',
			onDelete: 'SET NULL',
		});

		await queryInterface.addIndex('financial_transactions', ['feed_lot_id'], {
			name: 'idx_financial_transactions_feed_lot',
		});
	},

	down: async (queryInterface) => {
		await queryInterface.removeIndex('financial_transactions', 'idx_financial_transactions_feed_lot');
		await queryInterface.removeColumn('financial_transactions', 'feed_lot_id');
		await queryInterface.sequelize.query(
			'ALTER TABLE financial_transactions ALTER COLUMN species_id SET NOT NULL',
		);
	},
};
