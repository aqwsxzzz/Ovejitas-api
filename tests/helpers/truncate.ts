import { FastifyInstance } from 'fastify';

export async function truncateAllTables(app: FastifyInstance): Promise<void> {
	const tableNames = Object.values(app.db.models)
		.map((model) => (model as unknown as { tableName: string }).tableName)
		.filter(Boolean);

	if (tableNames.length === 0) return;

	await app.db.sequelize.query(
		`TRUNCATE TABLE ${tableNames.map((t) => `"${t}"`).join(', ')} RESTART IDENTITY CASCADE`,
	);
}
