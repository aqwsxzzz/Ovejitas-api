import { describe, it, expect } from 'vitest';
import { UserSerializer } from '../../src/resources/user/user.serializer';
import { encodeId } from '../../src/utils/id-hash-util';
import { UserModel } from '../../src/resources/user/user.model';

function makeUser(overrides?: Record<string, unknown>): UserModel {
	return {
		dataValues: {
			id: 1,
			displayName: 'Test User',
			email: 'test@example.com',
			password: 'hashed_password',
			isActive: true,
			role: 'user',
			language: 'en',
			lastVisitedFarmId: 5,
			createdAt: '2025-01-01T00:00:00.000Z',
			updatedAt: '2025-01-01T00:00:00.000Z',
			...overrides,
		},
	} as unknown as UserModel;
}

describe('UserSerializer', () => {
	describe('serialize', () => {
		it('encodes the user id as a hash', () => {
			const user = makeUser({ id: 42 });
			const result = UserSerializer.serialize(user);
			expect(result.id).toBe(encodeId(42));
		});

		it('encodes lastVisitedFarmId as a hash', () => {
			const user = makeUser({ lastVisitedFarmId: 10 });
			const result = UserSerializer.serialize(user);
			expect(result.lastVisitedFarmId).toBe(encodeId(10));
		});

		it('omits the password from the response', () => {
			const user = makeUser();
			const result = UserSerializer.serialize(user);
			expect(result.password).toBeUndefined();
		});

		it('includes display name and email', () => {
			const user = makeUser({ displayName: 'Alice', email: 'alice@test.com' });
			const result = UserSerializer.serialize(user);
			expect(result.displayName).toBe('Alice');
			expect(result.email).toBe('alice@test.com');
		});

		it('includes role, isActive, and language', () => {
			const user = makeUser({ role: 'admin', isActive: false, language: 'es' });
			const result = UserSerializer.serialize(user);
			expect(result.role).toBe('admin');
			expect(result.isActive).toBe(false);
			expect(result.language).toBe('es');
		});
	});

	describe('serializeMany', () => {
		it('serializes an array of users', () => {
			const users = [makeUser({ id: 1 }), makeUser({ id: 2 })];
			const result = UserSerializer.serializeMany(users);
			expect(result).toHaveLength(2);
			expect(result[0].id).toBe(encodeId(1));
			expect(result[1].id).toBe(encodeId(2));
		});
	});
});
