'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.createTable('feed_consumption_lots', {
			id: {
				type: Sequelize.INTEGER.UNSIGNED,
				autoIncrement: true,
				primaryKey: true,
				allowNull: false,
			},
			consumption_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: false,
				references: { model: 'feed_consumptions', key: 'id' },
				onUpdate: 'CASCADE',
				onDelete: 'CASCADE',
			},
			lot_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: false,
				references: { model: 'feed_lots', key: 'id' },
				onUpdate: 'CASCADE',
				onDelete: 'RESTRICT',
			},
			qty_drawn: {
				type: Sequelize.DECIMAL(12, 3),
				allowNull: false,
			},
			unit_price_snapshot: {
				type: Sequelize.DECIMAL(12, 2),
				allowNull: false,
			},
			created_at: {
				type: Sequelize.DATE,
				allowNull: false,
				defaultValue: Sequelize.NOW,
			},
		});

		await queryInterface.sequelize.query(
			'ALTER TABLE feed_consumption_lots ADD CONSTRAINT chk_feed_consumption_lots_qty_drawn_positive CHECK (qty_drawn > 0)',
		);

		await queryInterface.addIndex('feed_consumption_lots', ['consumption_id'], {
			name: 'idx_feed_consumption_lots_consumption',
		});
		await queryInterface.addIndex('feed_consumption_lots', ['lot_id'], {
			name: 'idx_feed_consumption_lots_lot',
		});
	},

	down: async (queryInterface) => {
		await queryInterface.removeIndex('feed_consumption_lots', 'idx_feed_consumption_lots_consumption');
		await queryInterface.removeIndex('feed_consumption_lots', 'idx_feed_consumption_lots_lot');
		await queryInterface.dropTable('feed_consumption_lots');
	},
};
