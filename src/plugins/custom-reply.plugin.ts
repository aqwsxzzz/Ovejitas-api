import { FastifyPluginAsync, FastifyReply } from 'fastify';
import fp from 'fastify-plugin';
import { SuccessMessage, ErrorMessage } from '../consts/error-messages';

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
        success<T = unknown>(data: T, message?: SuccessMessage): FastifyReply;
        error(message: ErrorMessage, statusCode?: number): FastifyReply;
        successWithPagination<T = unknown>(
            data: T[],
            pagination: PaginationMeta,
            message?: SuccessMessage
        ): FastifyReply;
        created<T = unknown>(data: T, message?: SuccessMessage): FastifyReply;
        noContent(message?: SuccessMessage): FastifyReply;
        accepted<T = unknown>(data: T, message?: SuccessMessage): FastifyReply;
        notFound(message?: ErrorMessage): FastifyReply;
        unauthorized(message?: ErrorMessage): FastifyReply;
        forbidden(message?: ErrorMessage): FastifyReply;
        badRequest(message?: ErrorMessage): FastifyReply;
        conflict(message?: ErrorMessage): FastifyReply;
    }
}

const customReplyPlugin: FastifyPluginAsync = async (fastify) => {
	// Success response (200)
	fastify.decorateReply('success', function<T = unknown>(
		this: FastifyReply,
		data: T,
		message: SuccessMessage = 'Success' as SuccessMessage,
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
		message: SuccessMessage = 'Created successfully' as SuccessMessage,
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
		message: ErrorMessage,
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
		message: SuccessMessage = 'Success' as SuccessMessage,
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
		message: SuccessMessage = 'No content' as SuccessMessage,
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
		message: SuccessMessage = 'Accepted' as SuccessMessage,
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
		message: ErrorMessage = 'User not found' as ErrorMessage,
	): FastifyReply {
		return this.error(message, 404);
	});

	fastify.decorateReply('unauthorized', function(
		this: FastifyReply,
		message: ErrorMessage = 'Unauthorized' as ErrorMessage,
	): FastifyReply {
		return this.error(message, 401);
	});

	fastify.decorateReply('forbidden', function(
		this: FastifyReply,
		message: ErrorMessage = 'Forbidden' as ErrorMessage,
	): FastifyReply {
		return this.error(message, 403);
	});

	fastify.decorateReply('badRequest', function(
		this: FastifyReply,
		message: ErrorMessage = 'Invalid input' as ErrorMessage,
	): FastifyReply {
		return this.error(message, 400);
	});

	fastify.decorateReply('conflict', function(
		this: FastifyReply,
		message: ErrorMessage = 'Resource already exists' as ErrorMessage,
	): FastifyReply {
		return this.error(message, 409);
	});
};

export default fp(customReplyPlugin, {
	name: 'custom-reply-plugin',
	fastify: '5.x',
});
