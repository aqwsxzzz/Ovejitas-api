'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.createTable('feeding_schedules', {
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
				onDelete: 'CASCADE',
			},
			flock_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: false,
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
			qty_per_day: {
				type: Sequelize.DECIMAL(12, 3),
				allowNull: false,
			},
			active_from: {
				type: Sequelize.DATEONLY,
				allowNull: false,
			},
			active_to: {
				type: Sequelize.DATEONLY,
				allowNull: true,
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
			'ALTER TABLE feeding_schedules ADD CONSTRAINT chk_feeding_schedules_qty_per_day_positive CHECK (qty_per_day > 0)',
		);
		await queryInterface.sequelize.query(
			'ALTER TABLE feeding_schedules ADD CONSTRAINT chk_feeding_schedules_date_range CHECK (active_to IS NULL OR active_to >= active_from)',
		);

		await queryInterface.addIndex('feeding_schedules', ['farm_id', 'flock_id'], {
			name: 'idx_feeding_schedules_farm_flock',
		});

		// Partial unique index: only one open-ended schedule per (flock, feed_type)
		await queryInterface.sequelize.query(
			'CREATE UNIQUE INDEX idx_feeding_schedules_flock_type_active ON feeding_schedules (flock_id, feed_type_id) WHERE active_to IS NULL',
		);
	},

	down: async (queryInterface) => {
		await queryInterface.sequelize.query('DROP INDEX IF EXISTS idx_feeding_schedules_flock_type_active');
		await queryInterface.removeIndex('feeding_schedules', 'idx_feeding_schedules_farm_flock');
		await queryInterface.dropTable('feeding_schedules');
	},
};
