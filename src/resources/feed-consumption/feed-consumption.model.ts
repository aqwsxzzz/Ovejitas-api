import { DataTypes, Model, Sequelize } from 'sequelize';
import { FeedConsumptionReason } from './feed-consumption.schema';

export interface FeedConsumptionAttributes {
	id: number;
	farmId: number;
	flockId: number | null;
	feedTypeId: number;
	consumedAt: string;
	qty: number;
	reason: FeedConsumptionReason;
	notes: string | null;
	createdBy: number;
	createdAt: string;
	updatedAt: string;
}

type FeedConsumptionCreationAttributes = Pick<
	FeedConsumptionAttributes,
	'farmId' | 'feedTypeId' | 'consumedAt' | 'qty' | 'reason' | 'createdBy'
> & Partial<Pick<FeedConsumptionAttributes, 'flockId' | 'notes'>>;

export class FeedConsumptionModel extends Model<FeedConsumptionAttributes, FeedConsumptionCreationAttributes> {
	declare id: number;
	declare farmId: number;
	declare flockId: number | null;
	declare feedTypeId: number;
	declare consumedAt: string;
	declare qty: number;
	declare reason: FeedConsumptionReason;
	declare notes: string | null;
	declare createdBy: number;
	declare createdAt: string;
	declare updatedAt: string;
}

export const initFeedConsumptionModel = (sequelize: Sequelize) => FeedConsumptionModel.init({
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
		onDelete: 'RESTRICT',
	},
	flockId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: true,
		field: 'flock_id',
		references: { model: 'flocks', key: 'id' },
		onDelete: 'RESTRICT',
	},
	feedTypeId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: false,
		field: 'feed_type_id',
		references: { model: 'feed_types', key: 'id' },
		onDelete: 'RESTRICT',
	},
	consumedAt: {
		type: DataTypes.DATEONLY,
		allowNull: false,
		field: 'consumed_at',
	},
	qty: {
		type: DataTypes.DECIMAL(12, 3),
		allowNull: false,
	},
	reason: {
		type: DataTypes.ENUM(...Object.values(FeedConsumptionReason)),
		allowNull: false,
	},
	notes: {
		type: DataTypes.TEXT,
		allowNull: true,
	},
	createdBy: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: false,
		field: 'created_by',
		references: { model: 'users', key: 'id' },
		onDelete: 'RESTRICT',
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
	tableName: 'feed_consumptions',
	modelName: 'FeedConsumption',
	timestamps: true,
});
