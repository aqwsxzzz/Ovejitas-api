import 'fastify';
import { Sequelize } from 'sequelize';
import { Database } from '../src/database';
import { AnimalService } from '../src/resources/animal/animal.service';
import { AnimalMeasurementService } from '../src/resources/animal-measurement/animal-measurement.service';
import { AuthService } from '../src/resources/auth/auth.service';
import { BreedService } from '../src/resources/breed/breed.service';
import { FarmService } from '../src/resources/farm/farm.service';
import { FarmMemberService } from '../src/resources/farm-member/farm-member.service';
import { InvitationService } from '../src/resources/invitation/invitation.service';
import { SpeciesService } from '../src/resources/species/species.service';
import { SpeciesTranslationService } from '../src/resources/species-translation/species-translation.service';
import { UserService } from '../src/resources/user/user.service';
import { ExpenseService } from '../src/resources/expense/expense.service';
import { FarmMemberRole } from '../src/resources/farm-member/farm-member.schema';

declare module 'fastify' {
	interface FastifyInstance {
		// Database
		db: Database;
		sequelize: Sequelize;

		// Services
		animalService: AnimalService;
		animalMeasurementService: AnimalMeasurementService;
		authService: AuthService;
		breedService: BreedService;
		farmService: FarmService;
		farmMemberService: FarmMemberService;
		invitationService: InvitationService;
		speciesService: SpeciesService;
		speciesTranslationService: SpeciesTranslationService;
		userService: UserService;
		expenseService: ExpenseService;

		// Helpers
		handleDbError: (error: unknown, reply: FastifyReply) => void;
		authenticate(request: FastifyRequest, reply: FastifyReply): Promise<void>;
		authorize(permissions: string[]): (request: FastifyRequest, reply: FastifyReply) => Promise<void>;
	}

	interface FastifyRequest {
		user: {
			id: number;
			email: string;
			role: string;
			farmRole: FarmMemberRole;
		} | null;
		lastVisitedFarmId: number;
		language: string;
	}
}
