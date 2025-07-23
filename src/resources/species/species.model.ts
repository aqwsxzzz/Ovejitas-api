import { DataTypes, Model, Sequelize } from 'sequelize';

export class SpeciesModel extends Model  {
	declare id: number;
	declare createdAt: string;
	declare updatedAt: string;
}

export const initSpeciesModel = (sequelize: Sequelize) => SpeciesModel.init({
	id: {
		type: DataTypes.INTEGER.UNSIGNED,
		autoIncrement: true,
		primaryKey: true,
		field: 'id',
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
},
{

	sequelize,
	tableName: 'species',
	modelName: 'Species',
	timestamps: true,

});
