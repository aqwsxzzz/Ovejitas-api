import { FastifyReply, FastifyRequest } from "fastify";
import { UserRole } from "../../models/user-model";

export const createUser = async (request: FastifyRequest, reply: FastifyReply) => {
	// Placeholder user object
	const user = {
		id: 1,
		displayName: "John Doe",
		email: "john@example.com",
		isActive: true,
		role: UserRole.USER,
		createdAt: new Date(),
		updatedAt: new Date(),
	};
	reply.code(201).send(user);
};

export const getUser = async (request: FastifyRequest, reply: FastifyReply) => {
	// Placeholder user object
	const user = {
		id: 1,
		displayName: "John Doe",
		email: "john@example.com",
		isActive: true,
		role: UserRole.USER,
		createdAt: new Date(),
		updatedAt: new Date(),
	};
	reply.send(user);
};

export const listUsers = async (request: FastifyRequest, reply: FastifyReply) => {
	// Placeholder user list
	const users = [
		{
			id: 1,
			displayName: "John Doe",
			email: "john@example.com",
			isActive: true,
			role: UserRole.USER,
			createdAt: new Date(),
			updatedAt: new Date(),
		},
		{
			id: 2,
			displayName: "Jane Smith",
			email: "jane@example.com",
			isActive: false,
			role: UserRole.ADMIN,
			createdAt: new Date(),
			updatedAt: new Date(),
		},
	];
	reply.send(users);
};

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
