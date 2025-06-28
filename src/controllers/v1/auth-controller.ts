import { FastifyReply, FastifyRequest } from "fastify";
import { User } from "../../models/user-model";
import { comparePassword } from "../../utils/password-util";
import { createJwtToken } from "../../utils/token-util";
import { serializeUser } from "../../serializers/user-serializer";
import { AuthSignUpBody } from "../../types/auth-types";
import { handleInvitationSignUp, handleDefaultSignUp } from "../../utils/auth-util";

const JWT_SECRET = process.env.JWT_SECRET || "your_jwt_secret";

export const signUp = async (request: FastifyRequest<{ Body: AuthSignUpBody }>, reply: FastifyReply) => {
	const transaction = await request.server.sequelize.transaction();
	try {
		const { email, invitationToken } = request.body;
		const existingUser = await User.findOne({ where: { email }, transaction });

		if (existingUser) {
			await transaction.rollback();
			return reply.code(400).send({ message: "Email already in use" });
		}
		let user;

		if (invitationToken) {
			try {
				user = await handleInvitationSignUp(request.body, transaction);
			} catch (err) {
				await transaction.rollback();
				return reply.code(400).send({ message: err instanceof Error ? err.message : "Invitation error" });
			}
			await transaction.commit();
			return reply.send({ message: "User created and added to farm via invitation" });
		} else {
			user = await handleDefaultSignUp(request.body, transaction);
			await transaction.commit();
			return reply.send({ message: "User created" });
		}
	} catch (error) {
		await transaction.rollback();
		reply.code(500).send({ message: "Internal server error", error: error instanceof Error ? error.message : "Unknown error" });
	}
};

export const login = async (request: FastifyRequest, reply: FastifyReply) => {
	try {
		const { email, password } = request.body as { email: string; password: string };
		const user = await User.findOne({ where: { email } });
		if (!user) {
			return reply.code(401).send({ message: "Invalid email or password" });
		}
		const isMatch = await comparePassword(password, user.password);
		if (!isMatch) {
			return reply.code(401).send({ message: "Invalid email or password" });
		}
		const token = createJwtToken({ id: user.id, email: user.email, role: user.role }, JWT_SECRET, { expiresIn: "1d" });
		reply
			.setCookie("jwt", token, {
				httpOnly: true,
				path: "/",
				sameSite: true,
				secure: process.env.NODE_ENV === "production",
				maxAge: 60 * 60 * 24, // 1 day
			})
			.send({ message: "Logged in", user: serializeUser(user) });
	} catch (error) {
		reply.code(500).send({ message: "Internal server error" });
	}
};

export const logout = async (request: FastifyRequest, reply: FastifyReply) => {
	reply.clearCookie("jwt", { path: "/" });
	reply.send({ message: "Logged out" });
};

export const getCurrentUser = async (request: FastifyRequest, reply: FastifyReply) => {
	try {
		// Check if user is set by the auth plugin
		if (!request.user) {
			return reply.code(401).send({ message: "Unauthorized" });
		}

		const user = await User.findByPk(request.user.id);
		console.log(" user:", user?.id);

		if (!user) {
			return reply.code(404).send({ message: "User not found" });
		}

		reply.send(serializeUser(user));
	} catch (error) {
		reply.code(401).send({ message: "Invalid or expired token" });
	}
};
