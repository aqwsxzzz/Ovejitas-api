import { DataTypes, Model, Sequelize } from 'sequelize';
import { FinancialTransaction, TransactionType } from './financial-transaction.schema';

type FinancialTransactionCreationAttributes = Pick<FinancialTransaction, 'farmId' | 'type' | 'amount' | 'speciesId' | 'date' | 'createdBy'> &
	Partial<Pick<FinancialTransaction, 'description'>>;

export class FinancialTransactionModel extends Model<FinancialTransaction, FinancialTransactionCreationAttributes> {
	declare id: number;
	declare farmId: number;
	declare type: string;
	declare amount: number;
	declare description: string | null;
	declare speciesId: number;
	declare date: string;
	declare createdBy: number;
	declare createdAt: string;
	declare updatedAt: string;
}

export const initFinancialTransactionModel = (sequelize: Sequelize) => FinancialTransactionModel.init({
	id: {
		type: DataTypes.INTEGER.UNSIGNED,
		autoIncrement: true,
		primaryKey: true,
		field: 'id',
	},
	farmId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: false,
		field: 'farm_id',
		references: {
			model: 'farms',
			key: 'id',
		},
	},
	type: {
		type: DataTypes.ENUM(...Object.values(TransactionType)),
		allowNull: false,
		field: 'type',
	},
	amount: {
		type: DataTypes.DECIMAL(12, 2),
		allowNull: false,
		field: 'amount',
		validate: {
			min: 0,
		},
	},
	description: {
		type: DataTypes.TEXT,
		allowNull: true,
		field: 'description',
	},
	speciesId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: false,
		field: 'species_id',
		references: {
			model: 'species',
			key: 'id',
		},
	},
	date: {
		type: DataTypes.DATEONLY,
		allowNull: false,
		field: 'date',
	},
	createdBy: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: false,
		field: 'created_by',
		references: {
			model: 'users',
			key: 'id',
		},
	},
	createdAt: {
		type: DataTypes.DATE,
		allowNull: false,
		defaultValue: DataTypes.NOW,
		field: 'created_at',
	},
	updatedAt: {
		type: DataTypes.DATE,
		allowNull: false,
		defaultValue: DataTypes.NOW,
		field: 'updated_at',
	},
}, {
	sequelize,
	tableName: 'financial_transactions',
	modelName: 'FinancialTransaction',
	timestamps: true,
	indexes: [
		{
			name: 'idx_financial_transactions_farm_date',
			fields: ['farm_id', 'date'],
		},
		{
			name: 'idx_financial_transactions_farm_type',
			fields: ['farm_id', 'type'],
		},
		{
			name: 'idx_financial_transactions_date',
			fields: ['date'],
		},
		{
			name: 'idx_financial_transactions_species',
			fields: ['species_id'],
		},
	],
});
