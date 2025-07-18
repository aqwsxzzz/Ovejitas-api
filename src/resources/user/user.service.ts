import { ERROR_MESSAGES, NotFoundError } from '../../consts/error-messages';
import { Database } from '../../database';
import { UserModel } from './user.model';
import {  UserUpdateInput } from './user.schema';

export class UserService {
	private db: Database;

	constructor(db: Database) {
		this.db = db;
	}

	async updateUser(id: number, userData: UserUpdateInput): Promise<UserModel | null> {
		const user = await this.db.models.User.findByPk(id);
		if (!user) return null;

		await user.update(userData);
		return user;
	}
	async deleteUser(id: number): Promise<void> {
		const user = await this.db.models.User.findByPk(id);
		if (!user) throw new NotFoundError(ERROR_MESSAGES.USER_NOT_FOUND);

		await user.destroy();
	}

}
