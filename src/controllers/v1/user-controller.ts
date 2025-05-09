import { FastifyReply, FastifyRequest } from "fastify";
import { User, UserRole } from "../../models/user-model";

export const updateUser = async (request: FastifyRequest, reply: FastifyReply) => {
	// Placeholder updated user object
	const user = {
		id: 1,
		displayName: "John Doe Updated",
		email: "john.updated@example.com",
		isActive: true,
		role: UserRole.USER,
		createdAt: new Date(),
		updatedAt: new Date(),
	};
	reply.send(user);
};

export const deleteUser = async (request: FastifyRequest, reply: FastifyReply) => {
	reply.send({ message: "Delete user (placeholder)" });
};
