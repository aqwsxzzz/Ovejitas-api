'use strict';

/** @type {import('sequelize-cli').Migration} */
module.exports = {
	async up (queryInterface, Sequelize) {
		await queryInterface.changeColumn('animals', 'birth_date', {
			type: Sequelize.DATE,
			allowNull: true,
		});

		await queryInterface.changeColumn('animals', 'name', {
			type: Sequelize.STRING(50),
			allowNull: true,
		});

		await queryInterface.changeColumn('animals', 'acquisition_date', {
			type: Sequelize.DATE,
			allowNull: true,
		});
	},

	async down (queryInterface, Sequelize) {
		await queryInterface.changeColumn('animals', 'birth_date', {
			type: Sequelize.DATE,
			allowNull: false,
		});

		await queryInterface.changeColumn('animals', 'name', {
			type: Sequelize.STRING(255),
			allowNull: false,
		});

		await queryInterface.changeColumn('animals', 'acquisition_date', {
			type: Sequelize.DATE,
			allowNull: false,
		});
	},
};
