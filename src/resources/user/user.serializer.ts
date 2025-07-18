import { encodeId } from '../../utils/id-hash-util';
import {  UserModel, UserRole } from './user.model';
import {  UserResponse } from './user.schema';

export class UserSerializer {
	static serialize(user: UserModel): UserResponse {
		return {
			id: encodeId(parseInt(user.dataValues.id)),
			displayName: user.dataValues.displayName ,
			email: user.dataValues.email ,
			isActive: user.dataValues.isActive as boolean,
			role: user.dataValues.role as UserRole,
			lastVisitedFarmId: encodeId(parseInt(user.dataValues.lastVisitedFarmId!)),
			createdAt: user.dataValues.createdAt,
			updatedAt: user.dataValues.updatedAt,
			language: user.dataValues.language,
		};
	}

	static serializeMany(users: UserModel[]): UserResponse[] {
		return users.map(user => this.serialize(user));
	}
}
