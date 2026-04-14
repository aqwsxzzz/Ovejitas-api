import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { Static, Type } from '@sinclair/typebox';
import { decodeId } from '../../utils/id-hash-util';
import {
	FeedConsumptionResponseSchema,
} from './feed-consumption.schema';
import { FeedConsumptionSerializer } from './feed-consumption.serializer';
import { FeedConsumptionWithLots } from './feed-consumption.service';
import { createPostEndpointSchema } from '../../utils/schema-builder';

const LogTodaysFeedingParamsSchema = Type.Object({
	flockId: Type.String(),
});

const LogTodaysFeedingBodySchema = Type.Object({
	date: Type.Optional(Type.String({ format: 'date' })),
}, {
	additionalProperties: false,
});

type LogTodaysFeedingParams = Static<typeof LogTodaysFeedingParamsSchema>;
type LogTodaysFeedingBody = Static<typeof LogTodaysFeedingBodySchema>;

const logTodaysFeedingSchema = createPostEndpointSchema({
	params: LogTodaysFeedingParamsSchema,
	body: LogTodaysFeedingBodySchema,
	dataSchema: Type.Array(FeedConsumptionResponseSchema),
	errorCodes: [400, 404, 409, 422],
});

const logTodaysFeedingRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {

	fastify.post('/flocks/:flockId/log-todays-feeding', { schema: logTodaysFeedingSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: LogTodaysFeedingParams; Body: LogTodaysFeedingBody }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const userId = request.user!.id;
			const flockId = decodeId(request.params.flockId);
			if (!flockId) return reply.error('Invalid flock ID', 400);

			const date = request.body?.date ?? new Date().toISOString().slice(0, 10);

			const created = await fastify.feedConsumptionService.logTodaysFeeding(farmId, flockId, userId, date);
			const serialized = FeedConsumptionSerializer.serializeMany(created as FeedConsumptionWithLots[]);
			reply.success(serialized);
		} catch (error) {
			if (error instanceof Error && error.name === 'InsufficientStockError') {
				return reply.error(error.message, 422);
			}
			fastify.handleDbError(error, reply);
		}
	});
};

export default logTodaysFeedingRoutes;
