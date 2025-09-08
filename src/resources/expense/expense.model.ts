import { DataTypes, Model, Sequelize } from 'sequelize';
import { Expense, ExpenseCategory, PaymentMethod, ExpenseStatus, QuantityUnit } from './expense.schema';

type ExpenseCreationAttributes = Pick<Expense, 'farmId' | 'date' | 'amount' | 'category' | 'createdBy'> &
	Partial<Pick<Expense, 'description' | 'speciesId' | 'breedId' | 'animalId' | 'lotId' | 'vendor' | 'paymentMethod' | 'invoiceNumber' | 'quantity' | 'quantityUnit' | 'unitCost' | 'status'>>;

export class ExpenseModel extends Model<Expense, ExpenseCreationAttributes> {
	declare id: number;
	declare farmId: number;
	declare date: string;
	declare amount: number;
	declare description: string | null;
	declare category: string;
	declare speciesId: number | null;
	declare breedId: number | null;
	declare animalId: number | null;
	declare lotId: number | null;
	declare vendor: string | null;
	declare paymentMethod: string | null;
	declare invoiceNumber: string | null;
	declare quantity: number | null;
	declare quantityUnit: string | null;
	declare unitCost: number | null;
	declare status: string | null;
	declare createdBy: number;
	declare createdAt: string;
	declare updatedAt: string;
}

export const initExpenseModel = (sequelize: Sequelize) => ExpenseModel.init({
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
	date: {
		type: DataTypes.DATEONLY,
		allowNull: false,
		field: 'date',
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
	category: {
		type: DataTypes.ENUM(...Object.values(ExpenseCategory)),
		allowNull: false,
		field: 'category',
	},
	speciesId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: true,
		field: 'species_id',
		references: {
			model: 'species',
			key: 'id',
		},
	},
	breedId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: true,
		field: 'breed_id',
		references: {
			model: 'breeds',
			key: 'id',
		},
	},
	animalId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: true,
		field: 'animal_id',
		references: {
			model: 'animals',
			key: 'id',
		},
	},
	lotId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: true,
		field: 'lot_id',
	},
	vendor: {
		type: DataTypes.STRING,
		allowNull: true,
		field: 'vendor',
	},
	paymentMethod: {
		type: DataTypes.ENUM(...Object.values(PaymentMethod)),
		allowNull: true,
		field: 'payment_method',
	},
	invoiceNumber: {
		type: DataTypes.STRING,
		allowNull: true,
		field: 'invoice_number',
	},
	quantity: {
		type: DataTypes.DECIMAL(10, 2),
		allowNull: true,
		field: 'quantity',
		validate: {
			min: 0,
		},
	},
	quantityUnit: {
		type: DataTypes.ENUM(...Object.values(QuantityUnit)),
		allowNull: true,
		field: 'quantity_unit',
	},
	unitCost: {
		type: DataTypes.DECIMAL(10, 2),
		allowNull: true,
		field: 'unit_cost',
		validate: {
			min: 0,
		},
	},
	status: {
		type: DataTypes.ENUM(...Object.values(ExpenseStatus)),
		allowNull: true,
		field: 'status',
		defaultValue: ExpenseStatus.Paid,
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
	tableName: 'expenses',
	modelName: 'Expense',
	timestamps: true,
	indexes: [
		{
			name: 'idx_expenses_farm_date',
			fields: ['farm_id', 'date'],
		},
		{
			name: 'idx_expenses_farm_category',
			fields: ['farm_id', 'category'],
		},
		{
			name: 'idx_expenses_date',
			fields: ['date'],
		},
	],
});
