import { FastifyReply, FastifyRequest } from "fastify";
import { User, UserLanguage } from "../../models/user-model";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import { serializeUser } from "../../serializers/user-serializer";
import { Farm } from "../../models/farm-model";
import { FarmMembers } from "../../models/farm-members-model";

const JWT_SECRET = process.env.JWT_SECRET || "your_jwt_secret";

export const signUp = async (request: FastifyRequest, reply: FastifyReply) => {
	try {
		const { displayName, email, password, language = "es" } = request.body as { displayName: string; email: string; password: string; language?: string };
		const existingUser = await User.findOne({ where: { email } });
		if (existingUser) {
			return reply.code(400).send({ message: "Email already in use" });
		}
		const saltRounds = 10;
		const hashedPassword = await bcrypt.hash(password, saltRounds);
		const user = await User.create({ displayName, email, password: hashedPassword, language: language as UserLanguage });

		// Create default farm for the user
		const farmName = language === "en" ? "My farm" : "Mi Granja";
		const farm = await Farm.create({ name: farmName });
		await FarmMembers.create({ farmId: farm.id, userId: user.id, role: "owner" });
		user.set("lastVisitedFarmId", farm.id);
		await user.save();

		reply.send({ message: "User created" });
	} catch (error) {
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
		const isMatch = await bcrypt.compare(password, user.password);
		if (!isMatch) {
			return reply.code(401).send({ message: "Invalid email or password" });
		}
		const token = jwt.sign({ id: user.id, email: user.email, role: user.role }, JWT_SECRET, { expiresIn: "1d" });
		reply
			.setCookie("jwt", token, {
				httpOnly: true,
				path: "/",
				sameSite: true,
				secure: process.env.NODE_ENV === "production",
				maxAge: 60 * 60 * 24, // 1 day
			})
			.send({ message: "Logged in" });
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
