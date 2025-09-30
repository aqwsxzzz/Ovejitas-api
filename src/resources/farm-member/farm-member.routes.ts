import { FastifyPluginAsync, FastifyRequest } from 'fastify';
import {
	createFarmMemberSchema,
	FarmMemberCreateInput,
	FarmMemberFarmParams,
	getFarmMembersSchema,
} from './farm-member.schema';
import { FarmMemberSerializer } from './farm-member.serializer';
import { decodeId } from '../../utils/id-hash-util';

const farmMemberRoutes: FastifyPluginAsync = async (fastify) => {
	fastify.post('/', {
		schema: createFarmMemberSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Body: FarmMemberCreateInput }>, reply) => {
		try {
			const { role, farmId, userId } = request.body;
			const farmMember = await fastify.farmMemberService.createFarmMember({ role, farmId, userId });
			reply.status(201).send(farmMember);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// Get all farm members for a specific farm
	fastify.get('/:farmId/members', {
		schema: getFarmMembersSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Params: FarmMemberFarmParams }>, reply) => {
		try {
			const { farmId } = request.params;
			const decodedFarmId = decodeId(farmId);

			if (!decodedFarmId) {
				return reply.status(404).send({
					status: 'error',
					message: 'Farm not found',
				});
			}

			const farmMembers = await fastify.farmMemberService.getFarmMembersWithUsers(decodedFarmId);
			const serializedMembers = FarmMemberSerializer.serializeMany(farmMembers, request.user?.farmRole);

			reply.success(serializedMembers, 'Farm members retrieved successfully');
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default farmMemberRoutes;
