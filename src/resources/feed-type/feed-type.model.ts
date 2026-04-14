import { DataTypes, Model, Sequelize } from 'sequelize';
import { FeedType } from './feed-type.schema';

type FeedTypeCreationAttributes = Pick<FeedType, 'farmId' | 'name'> & Partial<Pick<FeedType, 'notes'>>;

export class FeedTypeModel extends Model<FeedType, FeedTypeCreationAttributes> {
	declare id: number;
	declare farmId: number;
	declare name: string;
	declare notes: string | null;
	declare createdAt: string;
	declare updatedAt: string;
}

export const initFeedTypeModel = (sequelize: Sequelize) => FeedTypeModel.init({
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
	name: {
		type: DataTypes.STRING(120),
		allowNull: false,
	},
	notes: {
		type: DataTypes.TEXT,
		allowNull: true,
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
	tableName: 'feed_types',
	modelName: 'FeedType',
	timestamps: true,
	indexes: [
		{
			unique: true,
			fields: ['farm_id', 'name'],
			name: 'idx_feed_types_farm_name_unique',
		},
	],
});
