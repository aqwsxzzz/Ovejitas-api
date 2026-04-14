import { DataTypes, Model, Sequelize } from 'sequelize';
import { FeedLot } from './feed-lot.schema';

type FeedLotCreationAttributes = Pick<FeedLot, 'farmId' | 'feedTypeId' | 'qtyPurchased' | 'qtyRemaining' | 'unitPrice' | 'purchasedAt' | 'createdBy'> &
	Partial<Pick<FeedLot, 'supplier' | 'notes'>>;

export class FeedLotModel extends Model<FeedLot, FeedLotCreationAttributes> {
	declare id: number;
	declare farmId: number;
	declare feedTypeId: number;
	declare qtyPurchased: number;
	declare qtyRemaining: number;
	declare unitPrice: number;
	declare purchasedAt: string;
	declare supplier: string | null;
	declare notes: string | null;
	declare createdBy: number;
	declare createdAt: string;
	declare updatedAt: string;
}

export const initFeedLotModel = (sequelize: Sequelize) => FeedLotModel.init({
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
	feedTypeId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: false,
		field: 'feed_type_id',
		references: { model: 'feed_types', key: 'id' },
		onDelete: 'RESTRICT',
	},
	qtyPurchased: {
		type: DataTypes.DECIMAL(12, 3),
		allowNull: false,
		field: 'qty_purchased',
	},
	qtyRemaining: {
		type: DataTypes.DECIMAL(12, 3),
		allowNull: false,
		field: 'qty_remaining',
	},
	unitPrice: {
		type: DataTypes.DECIMAL(12, 2),
		allowNull: false,
		field: 'unit_price',
	},
	purchasedAt: {
		type: DataTypes.DATEONLY,
		allowNull: false,
		field: 'purchased_at',
	},
	supplier: {
		type: DataTypes.STRING(255),
		allowNull: true,
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
	tableName: 'feed_lots',
	modelName: 'FeedLot',
	timestamps: true,
	indexes: [
		{
			fields: ['farm_id', 'feed_type_id', 'purchased_at', 'id'],
			name: 'idx_feed_lots_fifo_drain',
		},
	],
});
