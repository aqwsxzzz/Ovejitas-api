import { FastifyPluginAsync, FastifyReply } from 'fastify';
import fp from 'fastify-plugin';

export interface ApiResponse<T = unknown> {
    status: 'success' | 'error';
    message: string;
    data?: T;
    meta: {
        timestamp: string;
        pagination?: PaginationMeta;
    };
}

export interface PaginationMeta {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
}

// Module augmentation with proper types
declare module 'fastify' {
    interface FastifyReply {
        success<T = unknown>(data: T, message?: string): FastifyReply;
        error(message: string, statusCode?: number): FastifyReply;
        successWithPagination<T = unknown>(
            data: T[],
            pagination: PaginationMeta,
            message?: string
        ): FastifyReply;
        created<T = unknown>(data: T, message?: string): FastifyReply;
        noContent(message?: string): FastifyReply;
        accepted<T = unknown>(data: T, message?: string): FastifyReply;
        notFound(message?: string): FastifyReply;
        unauthorized(message?: string): FastifyReply;
        forbidden(message?: string): FastifyReply;
        badRequest(message?: string): FastifyReply;
        conflict(message?: string): FastifyReply;
    }
}

const customReplyPlugin: FastifyPluginAsync = async (fastify) => {
	// Success response (200)
	fastify.decorateReply('success', function<T = unknown>(
		this: FastifyReply,
		data: T,
		message: string = 'Success',
	): FastifyReply {
		const response: ApiResponse<T> = {
			status: 'success',
			message,
			data,
			meta: {
				timestamp: new Date().toISOString(),
			},
		};
		return this.send(response);
	});

	// Created response (201)
	fastify.decorateReply('created', function<T = unknown>(
		this: FastifyReply,
		data: T,
		message: string = 'Created successfully',
	): FastifyReply {
		const response: ApiResponse<T> = {
			status: 'success',
			message,
			data,
			meta: {
				timestamp: new Date().toISOString(),
			},
		};
		return this.code(201).send(response);
	});

	// Error response (customizable status code)
	fastify.decorateReply('error', function(
		this: FastifyReply,
		message: string,
		statusCode: number = 400,
	): FastifyReply {
		const response: ApiResponse<never> = {
			status: 'error',
			message,
			meta: {
				timestamp: new Date().toISOString(),
			},
		};
		return this.code(statusCode).send(response);
	});

	// Success with pagination
	fastify.decorateReply('successWithPagination', function<T = unknown>(
		this: FastifyReply,
		data: T[],
		pagination: PaginationMeta,
		message: string = 'Success',
	): FastifyReply {
		const response: ApiResponse<T[]> = {
			status: 'success',
			message,
			data,
			meta: {
				pagination,
				timestamp: new Date().toISOString(),
			},
		};
		return this.send(response);
	});

	// No content response (204)
	fastify.decorateReply('noContent', function(
		this: FastifyReply,
		message: string = 'No content' ,
	): FastifyReply {
		const response: ApiResponse<never> = {
			status: 'success',
			message,
			meta: {
				timestamp: new Date().toISOString(),
			},
		};
		return this.code(204).send(response);
	});

	// Accepted response (202)
	fastify.decorateReply('accepted', function<T = unknown>(
		this: FastifyReply,
		data: T,
		message: string = 'Accepted' ,
	): FastifyReply {
		const response: ApiResponse<T> = {
			status: 'success',
			message,
			data,
			meta: {
				timestamp: new Date().toISOString(),
			},
		};
		return this.code(202).send(response);
	});

	// Specific error response helpers
	fastify.decorateReply('notFound', function(
		this: FastifyReply,
		message: string = 'User not found' ,
	): FastifyReply {
		return this.error(message, 404);
	});

	fastify.decorateReply('unauthorized', function(
		this: FastifyReply,
		message: string = 'Unauthorized' ,
	): FastifyReply {
		return this.error(message, 401);
	});

	fastify.decorateReply('forbidden', function(
		this: FastifyReply,
		message: string = 'Forbidden' ,
	): FastifyReply {
		return this.error(message, 403);
	});

	fastify.decorateReply('badRequest', function(
		this: FastifyReply,
		message: string = 'Invalid input' ,
	): FastifyReply {
		return this.error(message, 400);
	});

	fastify.decorateReply('conflict', function(
		this: FastifyReply,
		message: string = 'Resource already exists',
	): FastifyReply {
		return this.error(message, 409);
	});
};

export default fp(customReplyPlugin, {
	name: 'custom-reply-plugin',
	fastify: '5.x',
});
