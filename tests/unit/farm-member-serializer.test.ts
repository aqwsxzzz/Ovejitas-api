import { describe, it, expect } from 'vitest';
import { FarmMemberSerializer } from '../../src/resources/farm-member/farm-member.serializer';
import { encodeId } from '../../src/utils/id-hash-util';
import { FarmMemberWithUser } from '../../src/resources/farm-member/farm-member.schema';

function makeFarmMember(overrides?: Record<string, unknown>): FarmMemberWithUser {
	return {
		dataValues: {
			id: 1,
			farmId: 10,
			userId: 20,
			role: 'owner',
			createdAt: '2025-01-01T00:00:00.000Z',
			updatedAt: '2025-01-01T00:00:00.000Z',
			...overrides,
		},
		user: {
			id: 20,
			displayName: 'Test User',
			email: 'test@example.com',
		},
	} as unknown as FarmMemberWithUser;
}

describe('FarmMemberSerializer', () => {
	describe('serialize', () => {
		it('encodes id, farmId, and userId', () => {
			const member = makeFarmMember({ id: 1, farmId: 10, userId: 20 });
			const result = FarmMemberSerializer.serialize(member);
			expect(result.id).toBe(encodeId(1));
			expect(result.farmId).toBe(encodeId(10));
			expect(result.userId).toBe(encodeId(20));
		});

		it('includes role', () => {
			const member = makeFarmMember({ role: 'member' });
			const result = FarmMemberSerializer.serialize(member);
			expect(result.role).toBe('member');
		});

		it('includes nested user with encoded id', () => {
			const member = makeFarmMember();
			const result = FarmMemberSerializer.serialize(member);
			expect(result.user.id).toBe(encodeId(20));
			expect(result.user.displayName).toBe('Test User');
			expect(result.user.email).toBe('test@example.com');
		});
	});

	describe('serializeMany', () => {
		it('serializes an array of farm members', () => {
			const members = [makeFarmMember({ id: 1 }), makeFarmMember({ id: 2 })];
			const result = FarmMemberSerializer.serializeMany(members);
			expect(result).toHaveLength(2);
			expect(result[0].id).toBe(encodeId(1));
			expect(result[1].id).toBe(encodeId(2));
		});
	});
});
