'use strict';

module.exports = {
	up: async (queryInterface, Sequelize) => {
		await queryInterface.addColumn('farms', 'latitude', {
			type: Sequelize.DECIMAL(9, 6),
			allowNull: true,
		});
		await queryInterface.addColumn('farms', 'longitude', {
			type: Sequelize.DECIMAL(9, 6),
			allowNull: true,
		});
		await queryInterface.addColumn('farms', 'currency', {
			type: Sequelize.CHAR(3),
			allowNull: true,
		});

		await queryInterface.sequelize.query(
			'ALTER TABLE farms ADD CONSTRAINT farms_latitude_range CHECK (latitude IS NULL OR (latitude BETWEEN -90 AND 90))',
		);
		await queryInterface.sequelize.query(
			'ALTER TABLE farms ADD CONSTRAINT farms_longitude_range CHECK (longitude IS NULL OR (longitude BETWEEN -180 AND 180))',
		);
	},

	down: async (queryInterface) => {
		await queryInterface.sequelize.query('ALTER TABLE farms DROP CONSTRAINT IF EXISTS farms_longitude_range');
		await queryInterface.sequelize.query('ALTER TABLE farms DROP CONSTRAINT IF EXISTS farms_latitude_range');
		await queryInterface.removeColumn('farms', 'currency');
		await queryInterface.removeColumn('farms', 'longitude');
		await queryInterface.removeColumn('farms', 'latitude');
	},
};
