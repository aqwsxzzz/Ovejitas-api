import { Type, Static } from '@sinclair/typebox';
import { PaginationMeta } from '../plugins/custom-reply.plugin';

export const PaginationQueryProps = {
	page: Type.Optional(Type.Integer({ minimum: 1 })),
	limit: Type.Optional(Type.Integer({ minimum: 1, maximum: 100 })),
};

export const PaginationQuerySchema = Type.Object(PaginationQueryProps);

export type PaginationQuery = Static<typeof PaginationQuerySchema>;

export interface PaginationParams {
	page: number;
	limit: number;
	offset: number;
}

export interface PaginatedResult<T> {
	rows: T[];
	pagination: PaginationMeta;
}

export function parsePagination(query: Record<string, unknown>): PaginationParams | null {
	const page = Number(query.page);
	const limit = Number(query.limit);

	if (!query.page && !query.limit) {
		return null;
	}

	const resolvedPage = page > 0 ? page : 1;
	const resolvedLimit = limit > 0 ? Math.min(limit, 100) : 20;

	return {
		page: resolvedPage,
		limit: resolvedLimit,
		offset: (resolvedPage - 1) * resolvedLimit,
	};
}
