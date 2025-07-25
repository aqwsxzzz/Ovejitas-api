import { BaseService } from '../../services/base.service';
import { UserModel } from './user.model';
import {  UserUpdateInput } from './user.schema';

export class UserService extends BaseService {

	async updateUser(id: number, userData: UserUpdateInput): Promise<UserModel | null> {
		const user = await this.db.models.User.findByPk(id);
		if (!user) return null;

		await user.update(userData);
		return user;
	}

	async deleteUser(id: number): Promise<void> {
		const user = await this.db.models.User.findByPk(id);
		if (!user) throw new Error('User not found');

		await user.destroy();
	}

}
