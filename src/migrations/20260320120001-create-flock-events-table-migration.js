'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.createTable('flock_events', {
			id: {
				type: Sequelize.INTEGER.UNSIGNED,
				autoIncrement: true,
				primaryKey: true,
				allowNull: false,
			},
			flock_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: false,
				references: {
					model: 'flocks',
					key: 'id',
				},
				onUpdate: 'CASCADE',
				onDelete: 'CASCADE',
			},
			event_type: {
				type: Sequelize.ENUM('mortality', 'sale', 'cull', 'addition', 'transfer'),
				allowNull: false,
			},
			count: {
				type: Sequelize.INTEGER,
				allowNull: false,
			},
			date: {
				type: Sequelize.DATEONLY,
				allowNull: false,
			},
			reason: {
				type: Sequelize.STRING,
				allowNull: true,
			},
			recorded_by: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: true,
				references: {
					model: 'users',
					key: 'id',
				},
				onUpdate: 'CASCADE',
				onDelete: 'SET NULL',
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

		await queryInterface.addIndex('flock_events', ['flock_id', 'date'], {
			name: 'idx_flock_events_flock_date',
		});
		await queryInterface.addIndex('flock_events', ['flock_id', 'event_type'], {
			name: 'idx_flock_events_flock_type',
		});
	},

	down: async (queryInterface) => {
		await queryInterface.removeIndex('flock_events', 'idx_flock_events_flock_date');
		await queryInterface.removeIndex('flock_events', 'idx_flock_events_flock_type');
		await queryInterface.dropTable('flock_events');
	},
};
