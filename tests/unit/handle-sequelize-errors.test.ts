import { describe, it, expect } from 'vitest';
import {
	UniqueConstraintError,
	ValidationError,
	ForeignKeyConstraintError,
	DatabaseError,
	ValidationErrorItem,
} from 'sequelize';
import { handleSequelizeError } from '../../src/utils/handle-sequelize-errors';

describe('handleSequelizeError', () => {
	it('returns 400 with field name for UniqueConstraintError', () => {
		const error = new UniqueConstraintError({
			errors: [
				{ path: 'email', message: 'email must be unique' } as ValidationErrorItem,
			],
		});
		const result = handleSequelizeError(error);
		expect(result).toEqual({
			status: 400,
			message: 'email already exists',
			field: 'email',
		});
	});

	it('returns 400 for ValidationError', () => {
		const error = new ValidationError('Validation failed', [
			{ path: 'name', message: 'name cannot be empty' } as ValidationErrorItem,
		]);
		const result = handleSequelizeError(error);
		expect(result).toEqual({
			status: 400,
			message: 'name cannot be empty',
			field: 'name',
		});
	});

	it('returns 400 for ForeignKeyConstraintError', () => {
		const error = new ForeignKeyConstraintError({
			message: 'FK violation',
			parent: new Error('FK parent'),
			fields: ['species_id'],
		});
		const result = handleSequelizeError(error);
		expect(result).toEqual({
			status: 400,
			message: 'Referenced record does not exist',
		});
	});

	it('returns 500 for generic DatabaseError', () => {
		const error = new DatabaseError(new Error('connection lost'));
		const result = handleSequelizeError(error);
		expect(result).toEqual({
			status: 500,
			message: 'Database error occurred',
		});
	});

	it('returns 400 with message for generic Error', () => {
		const error = new Error('Something bad');
		const result = handleSequelizeError(error);
		expect(result).toEqual({
			status: 400,
			message: 'Something bad',
		});
	});

	it('returns null for non-Error values', () => {
		const result = handleSequelizeError('just a string');
		expect(result).toBeNull();
	});

	it('returns null for null input', () => {
		const result = handleSequelizeError(null);
		expect(result).toBeNull();
	});
});
