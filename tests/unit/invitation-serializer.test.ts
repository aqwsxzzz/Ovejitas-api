import { describe, it, expect } from 'vitest';
import { InvitationSerializer } from '../../src/resources/invitation/invitation.serializer';
import { encodeId } from '../../src/utils/id-hash-util';
import { InvitationModel } from '../../src/resources/invitation/invitation.model';

function makeInvitation(overrides?: Record<string, unknown>): InvitationModel {
	return {
		dataValues: {
			id: 1,
			email: 'invited@example.com',
			farmId: 10,
			role: 'member',
			status: 'pending',
			token: 'abc123token',
			createdAt: '2025-01-01T00:00:00.000Z',
			updatedAt: '2025-01-01T00:00:00.000Z',
			expiresAt: '2025-01-08T00:00:00.000Z',
			...overrides,
		},
	} as unknown as InvitationModel;
}

describe('InvitationSerializer', () => {
	describe('serialize', () => {
		it('encodes id and farmId', () => {
			const invitation = makeInvitation({ id: 5, farmId: 10 });
			const result = InvitationSerializer.serialize(invitation);
			expect(result.id).toBe(encodeId(5));
			expect(result.farmId).toBe(encodeId(10));
		});

		it('includes email, role, status, and token', () => {
			const invitation = makeInvitation();
			const result = InvitationSerializer.serialize(invitation);
			expect(result.email).toBe('invited@example.com');
			expect(result.role).toBe('member');
			expect(result.status).toBe('pending');
			expect(result.token).toBe('abc123token');
		});

		it('includes timestamps and expiresAt', () => {
			const invitation = makeInvitation();
			const result = InvitationSerializer.serialize(invitation);
			expect(result.createdAt).toBe('2025-01-01T00:00:00.000Z');
			expect(result.expiresAt).toBe('2025-01-08T00:00:00.000Z');
		});
	});

	describe('serializeMany', () => {
		it('serializes an array of invitations', () => {
			const invitations = [makeInvitation({ id: 1 }), makeInvitation({ id: 2 })];
			const result = InvitationSerializer.serializeMany(invitations);
			expect(result).toHaveLength(2);
			expect(result[0].id).toBe(encodeId(1));
			expect(result[1].id).toBe(encodeId(2));
		});
	});
});
