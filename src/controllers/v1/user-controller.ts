import { FastifyReply, FastifyRequest, RouteGenericInterface } from "fastify";
import { User } from "../../models/user-model";
import { IUserDeleteParams, IUserUpdateBody, IUserUpdateParams } from "../../types/user-types";
import { decodeId } from "../../utils/id-hash-util";
export interface UserUpdateRoute extends RouteGenericInterface {
	Params: IUserUpdateParams;
	Body: IUserUpdateBody;
}

export const updateUser = async (request: FastifyRequest<UserUpdateRoute>, reply: FastifyReply) => {
	const { id } = request.params;
	const { displayName, email, isActive, role } = request.body;

	const user = await User.findByPk(id);
	if (!user) {
		return reply.code(404).send({ message: "User not found" });
	}

	user.set({ displayName, email, isActive, role });

	await user.save();

	reply.send(user);
};

export interface UserDeleteRoute extends RouteGenericInterface {
	Params: IUserDeleteParams;
}

export const deleteUser = async (request: FastifyRequest<UserDeleteRoute>, reply: FastifyReply) => {
	const { id } = request.params;

	const user = await User.findByPk(decodeId(id));
	if (!user) {
		return reply.code(404).send({ message: "User not found" });
	}

	await user.destroy();

	reply.send({ message: "User deleted" });
};
