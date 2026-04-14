import { DataTypes, Model, Sequelize } from 'sequelize';

export interface FeedConsumptionLotAttributes {
	id: number;
	consumptionId: number;
	lotId: number;
	qtyDrawn: number;
	unitPriceSnapshot: number;
	createdAt: string;
}

type FeedConsumptionLotCreationAttributes = Pick<
	FeedConsumptionLotAttributes,
	'consumptionId' | 'lotId' | 'qtyDrawn' | 'unitPriceSnapshot'
>;

export class FeedConsumptionLotModel extends Model<FeedConsumptionLotAttributes, FeedConsumptionLotCreationAttributes> {
	declare id: number;
	declare consumptionId: number;
	declare lotId: number;
	declare qtyDrawn: number;
	declare unitPriceSnapshot: number;
	declare createdAt: string;
}

export const initFeedConsumptionLotModel = (sequelize: Sequelize) => FeedConsumptionLotModel.init({
	id: {
		type: DataTypes.INTEGER.UNSIGNED,
		autoIncrement: true,
		primaryKey: true,
		field: 'id',
	},
	consumptionId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: false,
		field: 'consumption_id',
		references: { model: 'feed_consumptions', key: 'id' },
		onDelete: 'CASCADE',
	},
	lotId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: false,
		field: 'lot_id',
		references: { model: 'feed_lots', key: 'id' },
		onDelete: 'RESTRICT',
	},
	qtyDrawn: {
		type: DataTypes.DECIMAL(12, 3),
		allowNull: false,
		field: 'qty_drawn',
	},
	unitPriceSnapshot: {
		type: DataTypes.DECIMAL(12, 2),
		allowNull: false,
		field: 'unit_price_snapshot',
	},
	createdAt: {
		type: DataTypes.DATE,
		allowNull: false,
		defaultValue: DataTypes.NOW,
		field: 'created_at',
	},
}, {
	sequelize,
	tableName: 'feed_consumption_lots',
	modelName: 'FeedConsumptionLot',
	timestamps: false,
});
