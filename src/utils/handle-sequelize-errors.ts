import {
	UniqueConstraintError,
	ValidationError,
	ForeignKeyConstraintError,
	DatabaseError,
} from 'sequelize';

interface ErrorResponse {
  status: number;
  message: string;
  field?: string;
}

export function handleSequelizeError(error: unknown): ErrorResponse | null {
	// Unique constraint (duplicate entry)
	if (error instanceof UniqueConstraintError) {
		const field = error.errors[0]?.path || 'field';
		return {
			status: 400,
			message: `${field} already exists`,
			field,
		};
	}

	// Validation errors
	if (error instanceof ValidationError) {
		return {
			status: 400,
			message: error.errors[0]?.message || 'Validation failed',
			field: error.errors[0]?.path ?? undefined,
		};
	}

	// Foreign key constraint
	if (error instanceof ForeignKeyConstraintError) {
		return {
			status: 400,
			message: 'Referenced record does not exist',

		};
	}

	// General database errors
	if (error instanceof DatabaseError) {
		return {
			status: 500,
			message: 'Database error occurred',
		};
	}

	if (error instanceof Error) {
		return  { status: 400, message: error.message };
	}

	// Not a Sequelize error
	return null;
}
