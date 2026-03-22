'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		// Drop the old expenses table
		await queryInterface.dropTable('expenses');

		// Drop orphaned ENUM types from expenses table
		await queryInterface.sequelize.query('DROP TYPE IF EXISTS "enum_expenses_category"');
		await queryInterface.sequelize.query('DROP TYPE IF EXISTS "enum_expenses_payment_method"');
		await queryInterface.sequelize.query('DROP TYPE IF EXISTS "enum_expenses_quantity_unit"');
		await queryInterface.sequelize.query('DROP TYPE IF EXISTS "enum_expenses_status"');

		// Create the new financial_transactions table
		await queryInterface.createTable('financial_transactions', {
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
			type: {
				type: Sequelize.ENUM('expense', 'income'),
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
			species_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: false,
				references: {
					model: 'species',
					key: 'id',
				},
				onUpdate: 'CASCADE',
				onDelete: 'RESTRICT',
			},
			date: {
				type: Sequelize.DATEONLY,
				allowNull: false,
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

		// Add performance indexes
		await queryInterface.sequelize.query(
			'CREATE INDEX "idx_financial_transactions_farm_date" ON "financial_transactions" ("farm_id", "date")'
		);
		await queryInterface.sequelize.query(
			'CREATE INDEX "idx_financial_transactions_farm_type" ON "financial_transactions" ("farm_id", "type")'
		);
		await queryInterface.sequelize.query(
			'CREATE INDEX "idx_financial_transactions_date" ON "financial_transactions" ("date")'
		);
		await queryInterface.sequelize.query(
			'CREATE INDEX "idx_financial_transactions_species" ON "financial_transactions" ("species_id")'
		);
	},

	down: async (queryInterface, Sequelize) => {
		// Remove indexes
		await queryInterface.removeIndex('financial_transactions', 'idx_financial_transactions_farm_date');
		await queryInterface.removeIndex('financial_transactions', 'idx_financial_transactions_farm_type');
		await queryInterface.removeIndex('financial_transactions', 'idx_financial_transactions_date');
		await queryInterface.removeIndex('financial_transactions', 'idx_financial_transactions_species');

		// Drop financial_transactions table
		await queryInterface.dropTable('financial_transactions');

		// Drop the ENUM type
		await queryInterface.sequelize.query('DROP TYPE IF EXISTS "enum_financial_transactions_type"');

		// Recreate the original expenses table
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

		await queryInterface.sequelize.query('CREATE INDEX IF NOT EXISTS "idx_expenses_farm_date" ON "expenses" ("farm_id", "date")');
		await queryInterface.sequelize.query('CREATE INDEX IF NOT EXISTS "idx_expenses_farm_category" ON "expenses" ("farm_id", "category")');
		await queryInterface.sequelize.query('CREATE INDEX IF NOT EXISTS "idx_expenses_date" ON "expenses" ("date")');
	},
};
