'use strict';

module.exports = {
	up: async (queryInterface) => {
		await queryInterface.removeIndex('egg_collections', 'idx_egg_collections_flock_date_unique');
		await queryInterface.addIndex('egg_collections', ['flock_id', 'date'], {
			name: 'idx_egg_collections_flock_date',
		});
	},

	down: async (queryInterface) => {
		await queryInterface.removeIndex('egg_collections', 'idx_egg_collections_flock_date');
		await queryInterface.addIndex('egg_collections', ['flock_id', 'date'], {
			unique: true,
			name: 'idx_egg_collections_flock_date_unique',
		});
	},
};
