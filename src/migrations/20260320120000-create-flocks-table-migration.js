'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.createTable('flocks', {
			id: {
				type: Sequelize.INTEGER.UNSIGNED,
				autoIncrement: true,
				primaryKey: true,
				allowNull: false,
			},
			farm_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: false,
				references: {
					model: 'farms',
					key: 'id',
				},
				onUpdate: 'CASCADE',
				onDelete: 'CASCADE',
			},
			species_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: false,
				references: {
					model: 'species',
					key: 'id',
				},
				onUpdate: 'CASCADE',
				onDelete: 'CASCADE',
			},
			breed_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: false,
				references: {
					model: 'breeds',
					key: 'id',
				},
				onUpdate: 'CASCADE',
				onDelete: 'CASCADE',
			},
			name: {
				type: Sequelize.STRING,
				allowNull: false,
			},
			flock_type: {
				type: Sequelize.ENUM('layers', 'broilers', 'dual_purpose', 'general'),
				allowNull: false,
			},
			initial_count: {
				type: Sequelize.INTEGER,
				allowNull: false,
			},
			current_count: {
				type: Sequelize.INTEGER,
				allowNull: false,
			},
			status: {
				type: Sequelize.ENUM('active', 'sold', 'culled', 'completed'),
				allowNull: false,
				defaultValue: 'active',
			},
			start_date: {
				type: Sequelize.DATEONLY,
				allowNull: false,
			},
			end_date: {
				type: Sequelize.DATEONLY,
				allowNull: true,
			},
			house_name: {
				type: Sequelize.STRING,
				allowNull: true,
			},
			acquisition_type: {
				type: Sequelize.ENUM('hatched', 'purchased', 'other'),
				allowNull: false,
			},
			age_at_acquisition_weeks: {
				type: Sequelize.INTEGER,
				allowNull: true,
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

		await queryInterface.addIndex('flocks', ['farm_id', 'name'], {
			unique: true,
			name: 'idx_flocks_farm_name_unique',
		});
		await queryInterface.addIndex('flocks', ['farm_id', 'status'], {
			name: 'idx_flocks_farm_status',
		});
		await queryInterface.addIndex('flocks', ['farm_id', 'species_id'], {
			name: 'idx_flocks_farm_species',
		});
	},

	down: async (queryInterface) => {
		await queryInterface.removeIndex('flocks', 'idx_flocks_farm_name_unique');
		await queryInterface.removeIndex('flocks', 'idx_flocks_farm_status');
		await queryInterface.removeIndex('flocks', 'idx_flocks_farm_species');
		await queryInterface.dropTable('flocks');
	},
};
