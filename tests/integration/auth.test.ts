import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { FastifyInstance } from 'fastify';
import { createTestApp } from '../helpers/build-app';
import { createAuthenticatedUser } from '../helpers/auth';
import { truncateAllTables } from '../helpers/truncate';

describe('Auth endpoints', () => {
	let app: FastifyInstance;

	beforeAll(async () => {
		app = await createTestApp();
	});

	afterEach(async () => {
		await truncateAllTables(app);
	});

	afterAll(async () => {
		await app.close();
	});

	describe('POST /api/v1/auth/signup', () => {
		it('creates a new user and returns user data', async () => {
			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/auth/signup',
				payload: {
					email: 'newuser@example.com',
					password: 'password123',
					displayName: 'New User',
				},
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
			expect(body.data.email).toBe('newuser@example.com');
			expect(body.data.displayName).toBe('New User');
			expect(body.data.password).toBeUndefined();
		});

		it('rejects duplicate email', async () => {
			await app.inject({
				method: 'POST',
				url: '/api/v1/auth/signup',
				payload: {
					email: 'dupe@example.com',
					password: 'password123',
					displayName: 'First User',
				},
			});

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/auth/signup',
				payload: {
					email: 'dupe@example.com',
					password: 'password123',
					displayName: 'Second User',
				},
			});

			expect(response.statusCode).toBe(400);
			const body = response.json();
			expect(body.message).toContain('already in use');
		});
	});

	describe('POST /api/v1/auth/login', () => {
		it('returns success and sets jwt cookie on valid credentials', async () => {
			// Arrange: sign up first
			await app.inject({
				method: 'POST',
				url: '/api/v1/auth/signup',
				payload: {
					email: 'login@example.com',
					password: 'password123',
					displayName: 'Login User',
				},
			});

			// Act
			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/auth/login',
				payload: {
					email: 'login@example.com',
					password: 'password123',
				},
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
			expect(body.data.email).toBe('login@example.com');

			const setCookie = response.headers['set-cookie'];
			expect(setCookie).toBeDefined();
			expect(String(setCookie)).toContain('jwt=');
		});

		it('rejects invalid credentials', async () => {
			await app.inject({
				method: 'POST',
				url: '/api/v1/auth/signup',
				payload: {
					email: 'user@example.com',
					password: 'password123',
					displayName: 'Test User',
				},
			});

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/auth/login',
				payload: {
					email: 'user@example.com',
					password: 'wrongpassword',
				},
			});

			expect(response.statusCode).toBe(400);
			const body = response.json();
			expect(body.message).toContain('Invalid credentials');
		});
	});

	describe('GET /api/v1/auth/me', () => {
		it('returns current user data when authenticated', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/auth/me',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
			expect(body.data.email).toBe(user.email);
		});

		it('returns 401 when not authenticated', async () => {
			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/auth/me',
			});

			expect(response.statusCode).toBe(401);
		});
	});
});
