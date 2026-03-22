'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.createTable('egg_collections', {
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
			date: {
				type: Sequelize.DATEONLY,
				allowNull: false,
			},
			total_eggs: {
				type: Sequelize.INTEGER,
				allowNull: false,
			},
			broken_eggs: {
				type: Sequelize.INTEGER,
				allowNull: false,
				defaultValue: 0,
			},
			collected_by: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: true,
				references: {
					model: 'users',
					key: 'id',
				},
				onUpdate: 'CASCADE',
				onDelete: 'SET NULL',
			},
			notes: {
				type: Sequelize.TEXT,
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

		await queryInterface.addIndex('egg_collections', ['flock_id', 'date'], {
			unique: true,
			name: 'idx_egg_collections_flock_date_unique',
		});
	},

	down: async (queryInterface) => {
		await queryInterface.removeIndex('egg_collections', 'idx_egg_collections_flock_date_unique');
		await queryInterface.dropTable('egg_collections');
	},
};
