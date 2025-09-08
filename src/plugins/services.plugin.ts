import { FastifyInstance, FastifyPluginAsync } from 'fastify';
import fastifyPlugin from 'fastify-plugin';

// Import all services
import { AnimalService } from '../resources/animal/animal.service';
import { AnimalMeasurementService } from '../resources/animal-measurement/animal-measurement.service';
import { AuthService } from '../resources/auth/auth.service';
import { BreedService } from '../resources/breed/breed.service';
import { ExpenseService } from '../resources/expense/expense.service';
import { FarmService } from '../resources/farm/farm.service';
import { FarmMemberService } from '../resources/farm-member/farm-member.service';
import { InvitationService } from '../resources/invitation/invitation.service';
import { SpeciesService } from '../resources/species/species.service';
import { SpeciesTranslationService } from '../resources/species-translation/species-translation.service';
import { UserService } from '../resources/user/user.service';

const servicesPlugin: FastifyPluginAsync = async (fastify: FastifyInstance) => {
	// Register all services as Fastify decorators
	// This allows services to be accessed across all plugins via fastify.serviceName

	fastify.decorate('animalService', new AnimalService(fastify.db));
	fastify.decorate('animalMeasurementService', new AnimalMeasurementService(fastify.db));
	fastify.decorate('authService', new AuthService(fastify.db));
	fastify.decorate('breedService', new BreedService(fastify.db));
	fastify.decorate('expenseService', new ExpenseService(fastify.db));
	fastify.decorate('farmService', new FarmService(fastify.db));
	fastify.decorate('farmMemberService', new FarmMemberService(fastify.db));
	fastify.decorate('invitationService', new InvitationService(fastify.db));
	fastify.decorate('speciesService', new SpeciesService(fastify.db));
	fastify.decorate('speciesTranslationService', new SpeciesTranslationService(fastify.db));
	fastify.decorate('userService', new UserService(fastify.db));

	fastify.log.info('Services plugin registered successfully');
};

export default fastifyPlugin(servicesPlugin, {
	name: 'services-plugin',
	dependencies: ['database-plugin'],
});
