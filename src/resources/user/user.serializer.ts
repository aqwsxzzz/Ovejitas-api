import { encodeId } from '../../utils/id-hash-util';
import { UserLanguage, UserModel, UserRole } from './user.model';
import {  UserResponse } from './user.schema';

export class UserSerializer {
	static serialize(user: UserModel): UserResponse {
		return {
			id: encodeId((user.get('id') as number)),
			displayName: user.get('displayName') as string,
			email: user.get('email') as string,
			isActive: user.get('isActive') as boolean,
			role: user.get('role') as UserRole,
			lastVisitedFarmId: encodeId((user.get('lastVisitedFarmId') as number)),
			createdAt: user.get('createdAt') as string,
			updatedAt: user.get('updatedAt') as string,
			language: user.get('language') as UserLanguage,
		};
	}

	static serializeMany(users: UserModel[]): UserResponse[] {
		return users.map(user => this.serialize(user));
	}
}
