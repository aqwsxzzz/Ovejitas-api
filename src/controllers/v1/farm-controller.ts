import { FastifyReply, FastifyRequest } from 'fastify';
import { Farm } from '../../models/farm-model';
import { FarmMembers } from '../../models/farm-members-model';
import { FarmCreateRoute, FarmUpdateRoute, IFarmIdParam, FarmDeleteRoute } from '../../types/farm-types';
import { serializeFarm } from '../../serializers/farm-serializer';
import { decodeId } from '../../utils/id-hash-util';

export const createFarm = async (request: FastifyRequest<FarmCreateRoute>, reply: FastifyReply) => {
	const { name } = request.body;
	try {
		const farm = await Farm.create({ name });
		reply.code(201).send(serializeFarm(farm));
	} catch (error) {
		reply.code(500).send({ message: 'Failed to create farm', error: error instanceof Error ? error.message : error });
	}
};

export const getFarms = async (request: FastifyRequest, reply: FastifyReply) => {
	if (!request.user) {
		return reply.code(401).send({ message: 'Unauthorized' });
	}

	const farms = await Farm.findAll({
		include: [{
			model: FarmMembers,
			as: 'members',
			where: {
				userId: request.user.id,
			},
			required: true,
		}],
	});
	reply.send(farms.map(serializeFarm));
};

export const getFarmById = async (request: FastifyRequest<{ Params: IFarmIdParam }>, reply: FastifyReply) => {
	const { id } = request.params;
	const farm = await Farm.findByPk(decodeId(id));
	if (!farm) {
		return reply.code(404).send({ message: 'Farm not found' });
	}
	reply.send(serializeFarm(farm));
};

export const updateFarm = async (request: FastifyRequest<FarmUpdateRoute>, reply: FastifyReply) => {
	const { id } = request.params;
	const { name } = request.body;
	const farm = await Farm.findByPk(decodeId(id));
	if (!farm) {
		return reply.code(404).send({ message: 'Farm not found' });
	}
	farm.setDataValue('name', name);
	await farm.save();
	reply.send(serializeFarm(farm));
};

export const deleteFarm = async (request: FastifyRequest<FarmDeleteRoute>, reply: FastifyReply) => {
	const { id } = request.params;
	const farm = await Farm.findByPk(decodeId(id));
	if (!farm) {
		return reply.code(404).send({ message: 'Farm not found' });
	}
	await farm.destroy();
	reply.send({ message: 'Farm deleted' });
};
