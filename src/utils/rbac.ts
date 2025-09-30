import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { FarmMemberRole } from '../resources/farm-member/farm-member.schema';

export const permissions = {
	owner: [
		'animals:read',
		'animals:create',
		'animals:delete',
		'members:invite',
		'members:delete',
		'members:read',
		'expenses:read',
		'expenses:create',
		'expenses:delete',
	],
	member: [
		'animals:read',
		'animals:create',
		'members:read',
		'expenses:read',
		'expenses:create',
	],
} as const;

export type Permission = typeof permissions.owner[number] | typeof permissions.member[number];

/**
 * Get all permissions for a given role
 */
export function getPermissionsForRole(role: FarmMemberRole): readonly string[] {
	return permissions[role] || [];
}

/**
 * Check if a user role has a specific permission
 */
export function hasPermission(userRole: FarmMemberRole, requiredPermission: string): boolean {
	const userPermissions = getPermissionsForRole(userRole);
	return userPermissions.includes(requiredPermission);
}

/**
 * Check if a user role has all required permissions
 */
export function hasAllPermissions(userRole: FarmMemberRole, requiredPermissions: string[]): boolean {
	return requiredPermissions.every(permission => hasPermission(userRole, permission));
}

/**
 * Fastify decorator factory for permission-based authorization
 * Usage: preHandler: fastify.authorize(['animals:delete'])
 */
export function createAuthorizeDecorator(fastify: FastifyInstance) {
	return function authorize(requiredPermissions: string[]) {
		return async (request: FastifyRequest, reply: FastifyReply) => {
			// First authenticate the user
			await fastify.authenticate(request, reply);

			// Check if user has farmRole
			if (!request.user?.farmRole) {
				return reply.error('Access denied: No farm role', 403);
			}

			// Check permissions
			if (!hasAllPermissions(request.user.farmRole, requiredPermissions)) {
				return reply.error('Access denied: Insufficient permissions', 403);
			}
		};
	};
}
