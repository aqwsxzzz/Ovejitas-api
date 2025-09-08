'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.createTable('expenses', {
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
				onDelete: 'RESTRICT',
			},
			date: {
				type: Sequelize.DATEONLY,
				allowNull: false,
			},
			amount: {
				type: Sequelize.DECIMAL(12, 2),
				allowNull: false,
			},
			description: {
				type: Sequelize.TEXT,
				allowNull: true,
			},
			category: {
				type: Sequelize.ENUM('feed', 'veterinary', 'transport', 'equipment', 'labor', 'utilities', 'maintenance', 'other'),
				allowNull: false,
			},
			species_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: true,
				references: {
					model: 'species',
					key: 'id',
				},
				onUpdate: 'CASCADE',
				onDelete: 'SET NULL',
			},
			breed_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: true,
				references: {
					model: 'breeds',
					key: 'id',
				},
				onUpdate: 'CASCADE',
				onDelete: 'SET NULL',
			},
			animal_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: true,
				references: {
					model: 'animals',
					key: 'id',
				},
				onUpdate: 'CASCADE',
				onDelete: 'SET NULL',
			},
			lot_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: true,
			},
			vendor: {
				type: Sequelize.STRING,
				allowNull: true,
			},
			payment_method: {
				type: Sequelize.ENUM('cash', 'bank_transfer', 'credit_card', 'debit_card', 'check', 'other'),
				allowNull: true,
			},
			invoice_number: {
				type: Sequelize.STRING,
				allowNull: true,
			},
			quantity: {
				type: Sequelize.DECIMAL(10, 2),
				allowNull: true,
			},
			quantity_unit: {
				type: Sequelize.ENUM('kg', 'liters', 'units', 'boxes', 'bags', 'doses', 'hours', 'other'),
				allowNull: true,
			},
			unit_cost: {
				type: Sequelize.DECIMAL(10, 2),
				allowNull: true,
			},
			status: {
				type: Sequelize.ENUM('pending', 'paid', 'reimbursed'),
				allowNull: true,
				defaultValue: 'paid',
			},
			created_by: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: false,
				references: {
					model: 'users',
					key: 'id',
				},
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

		// Add indexes for better query performance
		await queryInterface.addIndex('expenses', ['farm_id', 'date'], {
			name: 'idx_expenses_farm_date',
		});

		await queryInterface.addIndex('expenses', ['farm_id', 'category'], {
			name: 'idx_expenses_farm_category',
		});

		await queryInterface.addIndex('expenses', ['date'], {
			name: 'idx_expenses_date',
		});
	},

	down: async (queryInterface) => {
		// Remove indexes
		await queryInterface.removeIndex('expenses', 'idx_expenses_farm_date');
		await queryInterface.removeIndex('expenses', 'idx_expenses_farm_category');
		await queryInterface.removeIndex('expenses', 'idx_expenses_date');

		// Drop the table
		await queryInterface.dropTable('expenses');
	},
};
