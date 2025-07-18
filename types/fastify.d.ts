import 'fastify';
import { Sequelize } from 'sequelize';
import { Database } from '../src/database';
import { UserService } from '../src/resources/user/user.service';
import { AuthService } from '../src/resources/auth/auth.service';

declare module 'fastify' {
	interface FastifyInstance {
		db: Database;
		sequelize: Sequelize;
		userService: UserService;
		authService: AuthService;
		handleDbError: (error: unknown, reply: FastifyReply) => void;
		authenticate(request: FastifyRequest, reply: FastifyReply): Promise<void>;
	}

	interface FastifyRequest {
		user: {
			id: number;
			email: string;
			role: string;
		} | null;
		lastVisitedFarmId: number;
		language: string;
	}
}
