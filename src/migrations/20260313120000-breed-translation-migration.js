'use strict';

/**
 * Migration to create the breed_translation table.
 * Mirrors the species_translation pattern for i18n support.
 */

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.createTable('breed_translation', {
			id: {
				type: Sequelize.INTEGER.UNSIGNED,
				autoIncrement: true,
				primaryKey: true,
				allowNull: false,
			},
			breed_id: {
				type: Sequelize.INTEGER.UNSIGNED,
				allowNull: false,
				references: {
					model: 'breeds',
					key: 'id',
				},
				onDelete: 'CASCADE',
			},
			language_code: {
				type: Sequelize.STRING(5),
				allowNull: false,
			},
			name: {
				type: Sequelize.STRING,
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

		// Add unique constraint for (breed_id, language_code)
		await queryInterface.addConstraint('breed_translation', {
			fields: ['breed_id', 'language_code'],
			type: 'unique',
			name: 'unique_breed_language',
		});

		// Note: no (name, language_code) constraint — different species can share breed names (e.g. "Other")
	},

	down: async (queryInterface, _Sequelize) => {
		await queryInterface.dropTable('breed_translation');
	},
};
