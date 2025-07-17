import { User, UserRole, UserLanguage } from '../models/user-model';
import { encodeId } from '../utils/id-hash-util';

export const userResponseSchema = {
	type: 'object',
	properties: {
		id: { type: 'string' },
		displayName: { type: 'string' },
		email: { type: 'string' },
		isActive: { type: 'boolean' },
		role: { type: 'string', enum: Object.values(UserRole) },
		language: { type: 'string', enum: Object.values(UserLanguage) },
		createdAt: { type: 'string', format: 'date-time' },
		updatedAt: { type: 'string', format: 'date-time' },
		lastVisitedFarmId: { type: 'string' },
	},
	required: ['id', 'displayName', 'email', 'isActive', 'role', 'language', 'createdAt', 'updatedAt', 'lastVisitedFarmId'],
	additionalProperties: false,
};

export function serializeUser(user: User) {
	return {
		id: encodeId(user.id),
		displayName: user.displayName,
		email: user.email,
		isActive: user.isActive,
		role: user.role,
		language: user.language,
		createdAt: user.createdAt,
		updatedAt: user.updatedAt,
		lastVisitedFarmId: user.lastVisitedFarmId ? encodeId(user.lastVisitedFarmId) : null,
	};
}
