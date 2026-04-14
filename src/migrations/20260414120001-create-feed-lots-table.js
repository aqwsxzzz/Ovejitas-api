'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.createTable('feed_lots', {
			id: {
				type: Sequelize.INTEGER.UNSIGNED,
				autoIncrement: true,
				primaryKey: true,
				allowNull: false,
			},
			farm_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: false,
				references: { model: 'farms', key: 'id' },
				onUpdate: 'CASCADE',
				onDelete: 'RESTRICT',
			},
			feed_type_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: false,
				references: { model: 'feed_types', key: 'id' },
				onUpdate: 'CASCADE',
				onDelete: 'RESTRICT',
			},
			qty_purchased: {
				type: Sequelize.DECIMAL(12, 3),
				allowNull: false,
			},
			qty_remaining: {
				type: Sequelize.DECIMAL(12, 3),
				allowNull: false,
			},
			unit_price: {
				type: Sequelize.DECIMAL(12, 2),
				allowNull: false,
			},
			purchased_at: {
				type: Sequelize.DATEONLY,
				allowNull: false,
			},
			supplier: {
				type: Sequelize.STRING(255),
				allowNull: true,
			},
			notes: {
				type: Sequelize.TEXT,
				allowNull: true,
			},
			created_by: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: false,
				references: { model: 'users', key: 'id' },
				onUpdate: 'CASCADE',
				onDelete: 'RESTRICT',
			},
			created_at: {
				type: Sequelize.DATE,
				allowNull: false,
				defaultValue: Sequelize.NOW,
			},
			updated_at: {
				type: Sequelize.DATE,
				allowNull: false,
				defaultValue: Sequelize.NOW,
			},
		});

		await queryInterface.sequelize.query(
			'ALTER TABLE feed_lots ADD CONSTRAINT chk_feed_lots_qty_purchased_positive CHECK (qty_purchased > 0)',
		);
		await queryInterface.sequelize.query(
			'ALTER TABLE feed_lots ADD CONSTRAINT chk_feed_lots_qty_remaining_bounds CHECK (qty_remaining >= 0 AND qty_remaining <= qty_purchased)',
		);
		await queryInterface.sequelize.query(
			'ALTER TABLE feed_lots ADD CONSTRAINT chk_feed_lots_unit_price_non_negative CHECK (unit_price >= 0)',
		);

		await queryInterface.addIndex('feed_lots', ['farm_id', 'feed_type_id', 'purchased_at', 'id'], {
			name: 'idx_feed_lots_fifo_drain',
		});
		await queryInterface.sequelize.query(
			'CREATE INDEX idx_feed_lots_available ON feed_lots (farm_id, feed_type_id) WHERE qty_remaining > 0',
		);
	},

	down: async (queryInterface) => {
		await queryInterface.sequelize.query('DROP INDEX IF EXISTS idx_feed_lots_available');
		await queryInterface.removeIndex('feed_lots', 'idx_feed_lots_fifo_drain');
		await queryInterface.dropTable('feed_lots');
	},
};
