import { DataTypes, Model, Sequelize } from 'sequelize';
import { EggPricing } from './egg-pricing.schema';

type EggPricingCreationAttributes = Pick<EggPricing, 'farmId' | 'pricePerEgg' | 'effectiveFrom'> &
	Partial<Pick<EggPricing, 'effectiveTo'>>;

export class EggPricingModel extends Model<EggPricing, EggPricingCreationAttributes> {
	declare id: number;
	declare farmId: number;
	declare pricePerEgg: number;
	declare effectiveFrom: string;
	declare effectiveTo: string | null;
	declare createdAt: string;
	declare updatedAt: string;
}

export const initEggPricingModel = (sequelize: Sequelize) => EggPricingModel.init({
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
		references: { model: 'farms', key: 'id' },
		onDelete: 'CASCADE',
	},
	pricePerEgg: {
		type: DataTypes.DECIMAL(10, 4),
		allowNull: false,
		field: 'price_per_egg',
	},
	effectiveFrom: {
		type: DataTypes.DATEONLY,
		allowNull: false,
		field: 'effective_from',
	},
	effectiveTo: {
		type: DataTypes.DATEONLY,
		allowNull: true,
		field: 'effective_to',
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
	tableName: 'egg_pricings',
	modelName: 'EggPricing',
	timestamps: true,
	indexes: [
		{
			fields: ['farm_id', 'effective_from'],
			name: 'idx_egg_pricings_farm_effective_from',
		},
	],
});
