'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.createTable('animals', {
			id: {
				type: Sequelize.INTEGER.UNSIGNED,
				autoIncrement: true,
				primaryKey: true,
				allowNull: false,
			},
			farm_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: false,
				references: { model: 'farms', key: 'id' },
				onDelete: 'CASCADE',
			},
			species_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: false,
				references: { model: 'species', key: 'id' },
				onDelete: 'CASCADE',
			},
			breed_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: true,
				references: { model: 'breeds', key: 'id' },
				onDelete: 'SET NULL',
			},
			name: {
				type: Sequelize.STRING,
				allowNull: false,
			},
			tag_number: {
				type: Sequelize.STRING,
				allowNull: true,
			},
			sex: {
				type: Sequelize.ENUM('male', 'female', 'unknown'),
				allowNull: false,
			},
			birth_date: {
				type: Sequelize.DATE,
				allowNull: false,
			},
			weight: {
				type: Sequelize.FLOAT,
				allowNull: true,
			},
			status: {
				type: Sequelize.ENUM('alive', 'sold', 'deceased', 'deleted'),
				allowNull: false,
			},
			reproductive_status: {
				type: Sequelize.ENUM('open', 'pregnant', 'lactating', 'other'),
				allowNull: false,
			},

			parent_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: true,
				references: { model: 'animals', key: 'id' },
				onDelete: 'SET NULL',
			},
			mother_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: true,
				references: { model: 'animals', key: 'id' },
				onDelete: 'SET NULL',
			},
			acquisition_type: {
				type: Sequelize.ENUM('born', 'purchased', 'other'),
				allowNull: false,
			},
			acquisition_date: {
				type: Sequelize.DATE,
				allowNull: false,
			},
			created_at: {
				type: Sequelize.DATE,
				allowNull: false,
				defaultValue: Sequelize.literal('CURRENT_TIMESTAMP'),
			},
			updated_at: {
				type: Sequelize.DATE,
				allowNull: false,
				defaultValue: Sequelize.literal('CURRENT_TIMESTAMP'),
			},
		});
		await queryInterface.addConstraint('animals', {
			fields: ['farm_id', 'tag_number'],
			type: 'unique',
			name: 'unique_farm_tag_number',
			where: {
				tag_number: { [Sequelize.Op.ne]: null },
			},
		});
	},

	/**
	 * @param {import('sequelize').QueryInterface} queryInterface
	 * @param {typeof import('sequelize')} Sequelize
	 */
	down: async (queryInterface) => {
		await queryInterface.dropTable('animals');
		await queryInterface.sequelize.query('DROP TYPE IF EXISTS "enum_animals_sex"');
		await queryInterface.sequelize.query('DROP TYPE IF EXISTS "enum_animals_status"');
		await queryInterface.sequelize.query('DROP TYPE IF EXISTS "enum_animals_reproductive_status"');
		await queryInterface.sequelize.query('DROP TYPE IF EXISTS "enum_animals_acquisition_type"');
	},
};
