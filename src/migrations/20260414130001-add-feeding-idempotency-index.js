'use strict';

module.exports = {
	up: async (queryInterface) => {
		// Idempotency guard for log-todays-feeding: only one 'feeding' consumption
		// per (flock, feed_type, day). Waste/transfer/adjustment rows are unaffected.
		await queryInterface.sequelize.query(
			"CREATE UNIQUE INDEX idx_feed_consumptions_feeding_idempotency ON feed_consumptions (flock_id, feed_type_id, consumed_at) WHERE reason = 'feeding'",
		);
	},

	down: async (queryInterface) => {
		await queryInterface.sequelize.query('DROP INDEX IF EXISTS idx_feed_consumptions_feeding_idempotency');
	},
};
