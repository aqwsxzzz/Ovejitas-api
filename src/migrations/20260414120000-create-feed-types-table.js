'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.createTable('feed_types', {
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
			name: {
				type: Sequelize.STRING(120),
				allowNull: false,
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

		await queryInterface.addIndex('feed_types', ['farm_id', 'name'], {
			unique: true,
			name: 'idx_feed_types_farm_name_unique',
		});
	},

	down: async (queryInterface) => {
		await queryInterface.removeIndex('feed_types', 'idx_feed_types_farm_name_unique');
		await queryInterface.dropTable('feed_types');
	},
};
