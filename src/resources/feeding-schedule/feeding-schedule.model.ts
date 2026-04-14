import { DataTypes, Model, Sequelize } from 'sequelize';
import { FeedingSchedule } from './feeding-schedule.schema';

type FeedingScheduleCreationAttributes = Pick<
	FeedingSchedule,
	'farmId' | 'flockId' | 'feedTypeId' | 'qtyPerDay' | 'activeFrom'
> & Partial<Pick<FeedingSchedule, 'activeTo'>>;

export class FeedingScheduleModel extends Model<FeedingSchedule, FeedingScheduleCreationAttributes> {
	declare id: number;
	declare farmId: number;
	declare flockId: number;
	declare feedTypeId: number;
	declare qtyPerDay: number;
	declare activeFrom: string;
	declare activeTo: string | null;
	declare createdAt: string;
	declare updatedAt: string;
}

export const initFeedingScheduleModel = (sequelize: Sequelize) => FeedingScheduleModel.init({
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
	flockId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: false,
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
	qtyPerDay: {
		type: DataTypes.DECIMAL(12, 3),
		allowNull: false,
		field: 'qty_per_day',
	},
	activeFrom: {
		type: DataTypes.DATEONLY,
		allowNull: false,
		field: 'active_from',
	},
	activeTo: {
		type: DataTypes.DATEONLY,
		allowNull: true,
		field: 'active_to',
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
	tableName: 'feeding_schedules',
	modelName: 'FeedingSchedule',
	timestamps: true,
});
