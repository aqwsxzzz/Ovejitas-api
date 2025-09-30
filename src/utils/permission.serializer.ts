import { FarmMemberRole } from '../resources/farm-member/farm-member.schema';
import { getPermissionsForRole } from './rbac';

export type EntityType = 'animal' | 'member' | 'expense' | 'farm';

/**
 * Get permissions for a specific entity type based on user's farm role
 */
export function getEntityPermissions(entityType: EntityType, userRole: FarmMemberRole): string[] {
	const allPermissions = getPermissionsForRole(userRole);

	// Filter permissions relevant to the entity type
	const entityPrefix = getEntityPrefix(entityType);
	return allPermissions.filter(permission =>
		permission.startsWith(`${entityPrefix}:`),
	);
}

/**
 * Helper to map entity types to permission prefixes
 */
function getEntityPrefix(entityType: EntityType): string {
	const prefixMap: Record<EntityType, string> = {
		animal: 'animals',
		member: 'members',
		expense: 'expenses',
		farm: 'farm',
	};

	return prefixMap[entityType];
}
