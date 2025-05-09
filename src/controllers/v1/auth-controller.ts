import { FastifyReply, FastifyRequest } from "fastify";
import { User } from "../../models/user-model";
import bcrypt from "bcryptjs";
// import jwt from "jsonwebtoken";

const JWT_SECRET = process.env.JWT_SECRET || "your_jwt_secret";

export const signUp = async (request: FastifyRequest, reply: FastifyReply) => {
	try {
		const { displayName, email, password } = request.body as User;
		const existingUser = await User.findOne({ where: { email } });
		if (existingUser) {
			return reply.code(400).send({ message: "Email already in use" });
		}
		const saltRounds = 10;
		const hashedPassword = await bcrypt.hash(password, saltRounds);
		const user = await User.create({ displayName, email, password: hashedPassword });
		// const token = jwt.sign({ id: user.id, email: user.email, role: user.role }, JWT_SECRET, { expiresIn: "1d" });
		reply
			// .setCookie("jwt", token, {
			// 	httpOnly: true,
			// 	path: "/",
			// 	sameSite: true,
			// 	secure: process.env.NODE_ENV === "production",
			// 	maxAge: 60 * 60 * 24, // 1 day
			// })
			// .code(201)
			.send({ user: { id: user.id, displayName: user.displayName, email: user.email, role: user.role } });
	} catch (error) {
		reply.code(500).send({ message: "Internal server error" });
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
		// const token = jwt.sign({ id: user.id, email: user.email, role: user.role }, JWT_SECRET, { expiresIn: "1d" });
		reply
			// .setCookie("jwt", token, {
			// 	httpOnly: true,
			// 	path: "/",
			// 	sameSite: true,
			// 	secure: process.env.NODE_ENV === "production",
			// 	maxAge: 60 * 60 * 24, // 1 day
			// })
			.send({ user: { id: user.id, displayName: user.displayName, email: user.email, role: user.role } });
	} catch (error) {
		reply.code(500).send({ message: "Internal server error" });
	}
};

export const logout = async (request: FastifyRequest, reply: FastifyReply) => {
	// reply.clearCookie("jwt", { path: "/" });
	reply.send({ message: "Logged out" });
};

export const getCurrentUser = async (request: FastifyRequest, reply: FastifyReply) => {
	// Passport will attach user to request if authenticated
	const user = (request as any).user;
	if (!user) {
		return reply.code(401).send({ message: "Unauthorized" });
	}
	reply.send({ user });
};
