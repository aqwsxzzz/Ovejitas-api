import { buildApp } from './app';

const start = async () => {
	try {
		const server = await buildApp({ logger: true });
		const port = Number(process.env.PORT) || 8081;
		await server.listen({ port, host: '0.0.0.0' });
		console.log(`Server is running at ${server.server.address()}`);

		console.log('📋 Registered routes:');
		console.log(server.printRoutes());
	} catch (err) {
		console.error(err);
		process.exit(1);
	}
};

start();
