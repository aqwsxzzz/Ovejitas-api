// auth.service.ts
import { Database } from '../../database';
import { comparePassword } from '../../utils/password-util';
import { createJwtToken } from '../../utils/token-util';
import { UserModel } from '../user/user.model';
import { UserLoginInput, UserSignupInput } from './auth.schema';
import { handleDefaultSignUp } from './auth-helpers';

const JWT_SECRET = process.env.JWT_SECRET || 'your_jwt_secret';

export class AuthService {
	private db: Database;

	constructor(db: Database) {
		this.db = db;
	}

	async login(data: UserLoginInput): Promise<{ user: UserModel, token: string }> {
		const user = await this.db.models.User.findOne({
			where: { email: data.email },
		});

		if (!user) {
			throw new Error('User not found');
		}

		const isPasswordValid = await comparePassword(data.password, user.dataValues.password);
		if (!isPasswordValid) {
			throw new Error('Invalid credentials');
		}

		const token = createJwtToken(
			{ id: user.dataValues.id, email: user.dataValues.email, role: user.dataValues.role },
			JWT_SECRET,
			{ expiresIn: '1d' },
		);

		return { user, token };
	}

	async signup(data: UserSignupInput): Promise<{ user: UserModel, message: string }> {
		// Start transaction
		const transaction = await this.db.sequelize.transaction();

		try {
			const { email, invitationToken } = data;

			// Check if user already exists
			const existingUser = await this.db.models.User.findOne({
				where: { email },
				transaction,
			});

			if (existingUser) {
				throw new Error('Email already in use');
			}

			let user: UserModel;
			let message: string;

			// if (invitationToken) {
			// 	user = await handleInvitationSignUp(data, this.db, transaction);
			// 	message = 'User created and added to farm via invitation';
			// } else {
			// 	user = await handleDefaultSignUp(data, this.db, transaction);
			// 	message = 'User created';
			// }

			user = await handleDefaultSignUp(data, this.db, transaction);
			message = 'User created';

			await transaction.commit();
			return { user, message };

		} catch (error) {
			await transaction.rollback();
			throw error; // Re-throw to be handled by the plugin
		}
	}

	async getCurrentUser(userId: number): Promise<UserModel> {
		const user = await this.db.models.User.findByPk(userId);

		if (!user) {
			throw new Error('User not found');
		}

		return user;
	}

	async logout() {

	}
}
