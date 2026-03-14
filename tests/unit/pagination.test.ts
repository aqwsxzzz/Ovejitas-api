import { describe, it, expect } from 'vitest';
import { parsePagination } from '../../src/utils/pagination';

describe('parsePagination', () => {
	it('returns null when no page or limit params are provided', () => {
		const result = parsePagination({});
		expect(result).toBeNull();
	});

	it('returns null when params are unrelated to pagination', () => {
		const result = parsePagination({ include: 'translations', order: 'id:asc' });
		expect(result).toBeNull();
	});

	it('calculates correct offset for page 1', () => {
		const result = parsePagination({ page: '1', limit: '10' });
		expect(result).toEqual({ page: 1, limit: 10, offset: 0 });
	});

	it('calculates correct offset for page 3', () => {
		const result = parsePagination({ page: '3', limit: '10' });
		expect(result).toEqual({ page: 3, limit: 10, offset: 20 });
	});

	it('caps limit at 100', () => {
		const result = parsePagination({ page: '1', limit: '500' });
		expect(result).toEqual({ page: 1, limit: 100, offset: 0 });
	});

	it('defaults page to 1 when invalid', () => {
		const result = parsePagination({ page: '-1', limit: '10' });
		expect(result).toEqual({ page: 1, limit: 10, offset: 0 });
	});

	it('defaults limit to 20 when invalid', () => {
		const result = parsePagination({ page: '1', limit: '-5' });
		expect(result).toEqual({ page: 1, limit: 20, offset: 0 });
	});

	it('handles page only without limit', () => {
		const result = parsePagination({ page: '2' });
		expect(result).toEqual({ page: 2, limit: 20, offset: 20 });
	});

	it('handles limit only without page', () => {
		const result = parsePagination({ limit: '5' });
		expect(result).toEqual({ page: 1, limit: 5, offset: 0 });
	});
});
