import { FastifyInstance } from 'fastify';
import { buildApp } from '../../src/app';

export async function createTestApp(): Promise<FastifyInstance> {
	const app = await buildApp({ logger: false });
	await app.ready();
	return app;
}
