'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.createTable('egg_pricings', {
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
			price_per_egg: {
				type: Sequelize.DECIMAL(10, 4),
				allowNull: false,
			},
			effective_from: {
				type: Sequelize.DATEONLY,
				allowNull: false,
			},
			effective_to: {
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
			'ALTER TABLE egg_pricings ADD CONSTRAINT egg_pricings_price_non_negative CHECK (price_per_egg >= 0)',
		);

		await queryInterface.sequelize.query(
			'ALTER TABLE egg_pricings ADD CONSTRAINT egg_pricings_date_order CHECK (effective_to IS NULL OR effective_to >= effective_from)',
		);

		await queryInterface.addIndex('egg_pricings', ['farm_id', 'effective_from'], {
			name: 'idx_egg_pricings_farm_effective_from',
		});

		// Enforce at most one open-ended price per farm.
		await queryInterface.sequelize.query(
			'CREATE UNIQUE INDEX idx_egg_pricings_farm_open_unique ON egg_pricings (farm_id) WHERE effective_to IS NULL',
		);
	},

	down: async (queryInterface) => {
		await queryInterface.sequelize.query('DROP INDEX IF EXISTS idx_egg_pricings_farm_open_unique');
		await queryInterface.removeIndex('egg_pricings', 'idx_egg_pricings_farm_effective_from');
		await queryInterface.dropTable('egg_pricings');
	},
};
