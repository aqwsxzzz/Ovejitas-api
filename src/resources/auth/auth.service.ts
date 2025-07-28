// auth.service.ts
import { comparePassword, hashPassword } from '../../utils/password-util';
import { createJwtToken } from '../../utils/token-util';
import { UserModel } from '../user/user.model';
import { UserLoginInput, UserSignupInput } from './auth.schema';
import { BaseService } from '../../services/base.service';
import { Transaction } from 'sequelize';
import { InvitationStatus } from '../invitation/invitation.schema';
import { UserLanguage } from '../user/user.schema';
import { FarmMemberRole } from '../farm-member/farm-member.schema';

const JWT_SECRET = process.env.JWT_SECRET || 'your_jwt_secret';

export class AuthService extends BaseService {

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

			if (invitationToken) {
				user = await this.handleInvitationSignUp(data, transaction);
				message = 'User created and added to farm via invitation';
			} else {
				user = await this.handleDefaultSignUp(data, transaction);
				message = 'User created';
			}

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

	private async  handleInvitationSignUp(body: UserSignupInput,   transaction: Transaction) {
		const { displayName, email, password, language = 'es', invitationToken } = body;
		const invitation = await this.db.models.Invitation.findOne({ where: { token: invitationToken, status: 'pending' }, transaction });

		if (!invitation) {
			throw new Error('Invalid or expired invitation token');
		}

		if (!invitation.dataValues.expiresAt || new Date(invitation.dataValues.expiresAt).getTime() < Date.now()) {
			invitation.setDataValue('status', InvitationStatus.EXPIRED);
			await invitation.save({ transaction });
			throw new Error('Invitation has expired');
		}
		const hashedPassword = await hashPassword(password);
		const user = await this.db.models.User.create({ displayName, email: email.toLowerCase(), password: hashedPassword, language: language as UserLanguage }, { transaction });

		await this.db.models.FarmMember.create({ farmId: (invitation.dataValues.farmId)!, userId: user.dataValues.id, role: invitation.dataValues.role }, { transaction });
		user.set('lastVisitedFarmId', (invitation.dataValues.farmId));
		await user.save({ transaction });
		invitation.setDataValue('status', InvitationStatus.ACCEPTED);
		await invitation.save({ transaction });
		return user;
	}

	private async  handleDefaultSignUp(body: UserSignupInput,   transaction: Transaction) {
		const { displayName, email, password, language = 'es' } = body;

		const hashedPassword = await hashPassword(password);

		const user = await this.db.models.User.create({ displayName, email: email.toLowerCase(), password: hashedPassword, language: language as UserLanguage }, { transaction });

		const farmName = language === 'en' ? 'My farm' : 'Mi Granja';

		const farm = await this.db.models.Farm.create({ name: farmName }, { transaction });

		await this.db.models.FarmMember.create({ farmId: farm.dataValues.id, userId: user.dataValues.id, role: FarmMemberRole.OWNER }, { transaction });

		user.setDataValue('lastVisitedFarmId', farm.dataValues.id);

		await user.save({ transaction });

		return user;
	}
}
