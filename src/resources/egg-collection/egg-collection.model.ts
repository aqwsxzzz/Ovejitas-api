import { DataTypes, Model, Sequelize } from 'sequelize';
import { EggCollection } from './egg-collection.schema';

type EggCollectionCreationAttributes = Pick<EggCollection, 'flockId' | 'date' | 'totalEggs'> & Partial<Pick<EggCollection, 'brokenEggs' | 'collectedBy' | 'notes'>>;

export class EggCollectionModel extends Model<EggCollection, EggCollectionCreationAttributes> {
	declare id: number;
	declare flockId: number;
	declare date: string;
	declare totalEggs: number;
	declare brokenEggs: number;
	declare collectedBy: number | null;
	declare notes: string | null;
	declare createdAt: string;
	declare updatedAt: string;
}

export const initEggCollectionModel = (sequelize: Sequelize) => EggCollectionModel.init({
	id: {
		type: DataTypes.INTEGER.UNSIGNED,
		autoIncrement: true,
		primaryKey: true,
		field: 'id',
	},
	flockId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: false,
		field: 'flock_id',
		references: { model: 'flocks', key: 'id' },
		onDelete: 'CASCADE',
	},
	date: {
		type: DataTypes.DATEONLY,
		allowNull: false,
	},
	totalEggs: {
		type: DataTypes.INTEGER,
		allowNull: false,
		field: 'total_eggs',
	},
	brokenEggs: {
		type: DataTypes.INTEGER,
		allowNull: false,
		field: 'broken_eggs',
		defaultValue: 0,
	},
	collectedBy: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: true,
		field: 'collected_by',
		references: { model: 'users', key: 'id' },
		onDelete: 'SET NULL',
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
	tableName: 'egg_collections',
	modelName: 'EggCollection',
	timestamps: true,
	indexes: [
		{
			unique: true,
			fields: ['flock_id', 'date'],
			name: 'idx_egg_collections_flock_date_unique',
		},
	],
});
