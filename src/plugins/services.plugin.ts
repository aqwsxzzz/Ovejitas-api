import { FastifyInstance, FastifyPluginAsync } from 'fastify';
import fastifyPlugin from 'fastify-plugin';

// Import all services
import { AnimalService } from '../resources/animal/animal.service';
import { AnimalMeasurementService } from '../resources/animal-measurement/animal-measurement.service';
import { AuthService } from '../resources/auth/auth.service';
import { BreedService } from '../resources/breed/breed.service';
import { BreedTranslationService } from '../resources/breed-translation/breed-translation.service';
import { FinancialTransactionService } from '../resources/financial-transaction/financial-transaction.service';
import { FarmService } from '../resources/farm/farm.service';
import { FarmMemberService } from '../resources/farm-member/farm-member.service';
import { InvitationService } from '../resources/invitation/invitation.service';
import { SpeciesService } from '../resources/species/species.service';
import { SpeciesTranslationService } from '../resources/species-translation/species-translation.service';
import { UserService } from '../resources/user/user.service';
import { FlockService } from '../resources/flock/flock.service';
import { FlockEventService } from '../resources/flock-event/flock-event.service';
import { EggCollectionService } from '../resources/egg-collection/egg-collection.service';
import { WeatherService } from '../resources/weather/weather.service';
import { FeedTypeService } from '../resources/feed-type/feed-type.service';
import { FeedLotService } from '../resources/feed-lot/feed-lot.service';
import { FeedConsumptionService } from '../resources/feed-consumption/feed-consumption.service';
import { FeedingScheduleService } from '../resources/feeding-schedule/feeding-schedule.service';
import { FeedReportService } from '../resources/feed-report/feed-report.service';

const servicesPlugin: FastifyPluginAsync = async (fastify: FastifyInstance) => {
	// Register all services as Fastify decorators
	// This allows services to be accessed across all plugins via fastify.serviceName

	fastify.decorate('animalService', new AnimalService(fastify.db));
	fastify.decorate('animalMeasurementService', new AnimalMeasurementService(fastify.db));
	fastify.decorate('authService', new AuthService(fastify.db));
	fastify.decorate('breedService', new BreedService(fastify.db));
	fastify.decorate('breedTranslationService', new BreedTranslationService(fastify.db));
	fastify.decorate('financialTransactionService', new FinancialTransactionService(fastify.db));
	fastify.decorate('farmService', new FarmService(fastify.db));
	fastify.decorate('farmMemberService', new FarmMemberService(fastify.db));
	fastify.decorate('invitationService', new InvitationService(fastify.db));
	fastify.decorate('speciesService', new SpeciesService(fastify.db));
	fastify.decorate('speciesTranslationService', new SpeciesTranslationService(fastify.db));
	fastify.decorate('userService', new UserService(fastify.db));
	fastify.decorate('flockService', new FlockService(fastify.db));
	fastify.decorate('flockEventService', new FlockEventService(fastify.db));
	fastify.decorate('eggCollectionService', new EggCollectionService(fastify.db));
	fastify.decorate('weatherService', new WeatherService());
	fastify.decorate('feedTypeService', new FeedTypeService(fastify.db));
	fastify.decorate('feedLotService', new FeedLotService(fastify.db));
	fastify.decorate('feedConsumptionService', new FeedConsumptionService(fastify.db));
	fastify.decorate('feedingScheduleService', new FeedingScheduleService(fastify.db));
	fastify.decorate('feedReportService', new FeedReportService(fastify.db));

	fastify.log.info('Services plugin registered successfully');
};

export default fastifyPlugin(servicesPlugin, {
	name: 'services-plugin',
	dependencies: ['database-plugin'],
});
