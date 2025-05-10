import { FastifyReply, FastifyRequest } from "fastify";
import { User } from "../../models/user-model";
import { UserDeleteRoute, UserUpdateRoute } from "../../types/user-types";
import { decodeId } from "../../utils/id-hash-util";
import { serializeUser } from "../../serializers/user-serializer";

export const updateUser = async (request: FastifyRequest<UserUpdateRoute>, reply: FastifyReply) => {
	const { id } = request.params;
	const { displayName, email, isActive, role, language } = request.body;

	const user = await User.findByPk(id);
	if (!user) {
		return reply.code(404).send({ message: "User not found" });
	}

	user.set({ displayName, email, isActive, role, language });

	await user.save();

	reply.send(serializeUser(user));
};

export const deleteUser = async (request: FastifyRequest<UserDeleteRoute>, reply: FastifyReply) => {
	const { id } = request.params;

	const user = await User.findByPk(decodeId(id));
	if (!user) {
		return reply.code(404).send({ message: "User not found" });
	}

	await user.destroy();

	reply.send({ message: "User deleted" });
};
