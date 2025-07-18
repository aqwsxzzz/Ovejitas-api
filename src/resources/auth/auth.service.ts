import { BadRequestError, ERROR_MESSAGES, NotFoundError } from '../../consts/error-messages';
import { Database } from '../../database';
import { comparePassword } from '../../utils/password-util';
import { createJwtToken } from '../../utils/token-util';
import { UserModel } from '../user/user.model';
import { UserLoginInput } from './auth.schema';
import { FastifyReply, FastifyRequest } from 'fastify';

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
			throw new NotFoundError(ERROR_MESSAGES.USER_NOT_FOUND);
		}

		const isPasswordValid = await comparePassword(data.password, user.dataValues.password);
		if (!isPasswordValid) {
			throw new BadRequestError(ERROR_MESSAGES.INVALID_CREDENTIALS);
		}

		const token = createJwtToken(
			{ id: user.dataValues.id, email: user.dataValues.email, role: user.dataValues.role },
			JWT_SECRET,
			{ expiresIn: '1d' },
		);

		return { user, token };
	}

	async logout(request: FastifyRequest, reply: FastifyReply) {
		reply.clearCookie('jwt', { path: '/' });
		reply.success('Logged out successfully');
	}

	async currentUser(request: FastifyRequest) {
		// At this point, request.user is guaranteed to exist because of the preHandler
		const user = await this.db.models.User.findByPk(request.user!.id);

		if (!user) {
			throw new NotFoundError(ERROR_MESSAGES.USER_NOT_FOUND);
		}

		return user;
	}
}
