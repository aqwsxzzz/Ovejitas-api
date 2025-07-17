// src/plugins/database.plugin.ts
import { FastifyInstance, FastifyPluginAsync } from 'fastify';
import fastifyPlugin from 'fastify-plugin';
import { initDatabase, Database } from '.';

const databasePlugin: FastifyPluginAsync = async (fastify: FastifyInstance) => {
	// Initialize your database using the initDatabase function
	const db: Database = await initDatabase();

	// Decorate fastify instance
	fastify.decorate('db', db);

	// Add close hook
	fastify.addHook('onClose', async () => {
		await db.sequelize.close(); // Use sequelize.close() instead of disconnect()
	});

	fastify.log.info('Database plugin registered successfully');
};

export default fastifyPlugin(databasePlugin, {
	name: 'database-plugin',
});
