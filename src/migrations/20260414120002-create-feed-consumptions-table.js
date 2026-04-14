'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.createTable('feed_consumptions', {
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
			flock_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: true,
				references: { model: 'flocks', key: 'id' },
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
			consumed_at: {
				type: Sequelize.DATEONLY,
				allowNull: false,
			},
			qty: {
				type: Sequelize.DECIMAL(12, 3),
				allowNull: false,
			},
			reason: {
				type: Sequelize.ENUM('feeding', 'waste', 'transfer', 'adjustment'),
				allowNull: false,
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
			'ALTER TABLE feed_consumptions ADD CONSTRAINT chk_feed_consumptions_qty_positive CHECK (qty > 0)',
		);
		await queryInterface.sequelize.query(
			"ALTER TABLE feed_consumptions ADD CONSTRAINT chk_feed_consumptions_flock_required CHECK (flock_id IS NOT NULL OR reason IN ('waste', 'adjustment'))",
		);

		await queryInterface.addIndex('feed_consumptions', ['farm_id', 'flock_id', 'consumed_at'], {
			name: 'idx_feed_consumptions_farm_flock_date',
		});
		await queryInterface.addIndex('feed_consumptions', ['farm_id', 'feed_type_id', 'consumed_at'], {
			name: 'idx_feed_consumptions_farm_type_date',
		});
	},

	down: async (queryInterface) => {
		await queryInterface.removeIndex('feed_consumptions', 'idx_feed_consumptions_farm_flock_date');
		await queryInterface.removeIndex('feed_consumptions', 'idx_feed_consumptions_farm_type_date');
		await queryInterface.dropTable('feed_consumptions');
		await queryInterface.sequelize.query('DROP TYPE IF EXISTS "enum_feed_consumptions_reason"');
	},
};
