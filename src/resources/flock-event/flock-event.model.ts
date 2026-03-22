import { DataTypes, Model, Sequelize } from 'sequelize';
import { FlockEvent, FlockEventType } from './flock-event.schema';

type FlockEventCreationAttributes = Pick<FlockEvent, 'flockId' | 'eventType' | 'count' | 'date'> & Partial<Pick<FlockEvent, 'reason' | 'recordedBy'>>;

export class FlockEventModel extends Model<FlockEvent, FlockEventCreationAttributes> {
	declare id: number;
	declare flockId: number;
	declare eventType: FlockEventType;
	declare count: number;
	declare date: string;
	declare reason: string | null;
	declare recordedBy: number | null;
	declare createdAt: string;
	declare updatedAt: string;
}

export const initFlockEventModel = (sequelize: Sequelize) => FlockEventModel.init({
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
	eventType: {
		type: DataTypes.ENUM(...Object.values(FlockEventType)),
		allowNull: false,
		field: 'event_type',
	},
	count: {
		type: DataTypes.INTEGER,
		allowNull: false,
		validate: {
			min: 1,
		},
	},
	date: {
		type: DataTypes.DATEONLY,
		allowNull: false,
	},
	reason: {
		type: DataTypes.STRING,
		allowNull: true,
	},
	recordedBy: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: true,
		field: 'recorded_by',
		references: { model: 'users', key: 'id' },
		onDelete: 'SET NULL',
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
	tableName: 'flock_events',
	modelName: 'FlockEvent',
	timestamps: true,
	indexes: [
		{
			fields: ['flock_id', 'date'],
			name: 'idx_flock_events_flock_date',
		},
		{
			fields: ['flock_id', 'event_type'],
			name: 'idx_flock_events_flock_type',
		},
	],
});
