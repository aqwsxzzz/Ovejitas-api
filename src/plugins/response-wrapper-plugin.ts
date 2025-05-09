import { FastifyPluginAsync } from "fastify";
import fp from "fastify-plugin";

const responseWrapperPlugin: FastifyPluginAsync = async (fastify) => {
	console.log("a");
	fastify.addHook("onSend", async (request, reply, payload) => {
		console.log("b");
		if (reply.getHeader("content-type")?.toString().includes("application/json")) {
			let data;
			try {
				data = typeof payload === "string" ? JSON.parse(payload) : payload;
			} catch {
				data = payload;
			}

			const code = reply.statusCode;
			let status: "success" | "error" | "fail";
			if (code >= 200 && code < 300) status = "success";
			else if (code >= 400 && code < 500) status = "fail";
			else status = "error";

			const message = status === "success" ? "Request successful" : status === "fail" ? "Request failed" : "Internal server error";

			const wrapped = {
				status,
				data,
				message,
			};
			return JSON.stringify(wrapped);
		}
		return payload;
	});
};

export default fp(responseWrapperPlugin);
