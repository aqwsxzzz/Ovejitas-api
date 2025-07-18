import 'fastify';
import { Sequelize } from 'sequelize';
import { Database } from '../src/database';
import { UserService } from '../src/resources/user/user.service';
import { AuthService } from '../src/resources/auth/auth.service';
import { FarmMemberService } from '../src/resources/farm-member/farm-member.service';

declare module 'fastify' {
	interface FastifyInstance {
		db: Database;
		sequelize: Sequelize;
		userService: UserService;
		authService: AuthService;
		farmService: FarmService;
		farmMemberService: FarmMemberService
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
