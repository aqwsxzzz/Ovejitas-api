import { FastifyPluginAsync, FastifyRequest } from 'fastify';
import {
	createFarmSchema,
	deleteFarmSchema,
	FarmCreateInput,
	FarmListQuery,
	FarmParams,
	FarmUpdateInput,
	getFarmSchema,
	listCurrenciesSchema,
	listFarmsSchema,
	updateFarmSchema,
} from './farm.schema';
import { FarmSerializer } from './farm.serializer';
import { decodeId } from '../../utils/id-hash-util';
import { parsePagination } from '../../utils/pagination';
import { SUPPORTED_CURRENCIES } from './currencies';

const farmRoutes: FastifyPluginAsync = async (fastify) => {
	// Create Farm
	fastify.post('/', {
		schema: createFarmSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Body: FarmCreateInput }>, reply) => {
		try {
			const farmData = request.body;
			const newFarm = await fastify.farmService.createFarm(farmData, request.user!.id);
			const serializedFarm = FarmSerializer.serialize(newFarm);
			reply.success(serializedFarm, 'Farm created successfully');
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// Get Farms
	fastify.get('/', {
		schema: listFarmsSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Querystring: FarmListQuery }>, reply) => {
		try {
			const pagination = parsePagination(request.query);
			const result = await fastify.farmService.getFarms(request.user!.id, pagination);
			const serializedFarms = FarmSerializer.serializeMany(result.rows);
			reply.successWithPagination(serializedFarms, result.pagination);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// Get Farm
	fastify.get('/:farmId', {
		schema: getFarmSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Params: FarmParams }>, reply) => {
		try {
			const { farmId } = request.params;
			const decodedFarmId = decodeId(farmId);
			if (!decodedFarmId) {
				return reply.error('Invalid farm ID', 400);
			}

			const isMember = await fastify.farmMemberService.isMember(request.user!.id, decodedFarmId);
			if (!isMember) {
				return reply.error('Farm not found', 404);
			}

			const lastVisitedFarmId = request.lastVisitedFarmId;
			const farm = await fastify.farmService.getFarm(decodedFarmId);

			if (request.user && lastVisitedFarmId !== decodedFarmId) {
				await fastify.userService.updateLastVisitedFarm(request.user.id, decodedFarmId);
			}

			const serializedFarm = FarmSerializer.serialize(farm);
			reply.success(serializedFarm, 'Farm retrieved successfully');
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// List supported currencies (used by the farm settings UI)
	fastify.get('/currencies', {
		schema: listCurrenciesSchema,
		preHandler: fastify.authenticate,
	}, async (_request, reply) => {
		reply.success([...SUPPORTED_CURRENCIES]);
	});

	// Update Farm — owner only
	fastify.post('/:farmId', {
		schema: updateFarmSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Params: FarmParams, Body: FarmUpdateInput }>, reply) => {
		try {
			const { farmId } = request.params;
			const farmData = request.body;
			const decodedFarmId = decodeId(farmId);
			if (!decodedFarmId) {
				return reply.error('Invalid farm ID', 400);
			}

			const isOwner = await fastify.farmMemberService.isOwner(request.user!.id, decodedFarmId);
			if (!isOwner) {
				return reply.error('Only farm owners can update farm settings', 403);
			}

			const farm = await fastify.farmService.updateFarm(decodedFarmId, farmData);
			const serializedFarm = FarmSerializer.serialize(farm);
			reply.success(serializedFarm, 'Farm updated successfully');
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// Delete Farm — owner only
	fastify.delete('/:farmId', {
		schema: deleteFarmSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Params: FarmParams }>, reply) => {
		try {
			const { farmId } = request.params;
			const decodedFarmId = decodeId(farmId);
			if (!decodedFarmId) {
				return reply.error('Invalid farm ID', 400);
			}

			const isOwner = await fastify.farmMemberService.isOwner(request.user!.id, decodedFarmId);
			if (!isOwner) {
				return reply.error('Only farm owners can delete farms', 403);
			}

			await fastify.farmService.deleteFarm(decodedFarmId);
			reply.success('Farm deleted successfully');
		} catch (error) {
			fastify.log.error(error, 'Error deleting farm');
			fastify.handleDbError(error, reply);
		}
	});
};

export default farmRoutes;
