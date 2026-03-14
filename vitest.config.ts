import { defineConfig } from 'vitest/config';

export default defineConfig({
	test: {
		globals: true,
		include: ['tests/**/*.test.ts'],
		setupFiles: ['tests/setup.ts'],
		testTimeout: 10000,
		hookTimeout: 30000,
		fileParallelism: false,
		pool: 'forks',
		poolOptions: {
			forks: {
				execArgv: ['--import', 'tsx'],
			},
		},
	},
});
