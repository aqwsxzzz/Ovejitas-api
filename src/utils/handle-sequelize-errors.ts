import {
	UniqueConstraintError,
	ValidationError,
	ForeignKeyConstraintError,
	DatabaseError,
} from 'sequelize';
import { BadRequestError, ConflictError, ERROR_MESSAGES, ErrorMessage, ForbiddenError, NotFoundError, UnauthorizedError } from '../consts/error-messages';

interface ErrorResponse {
  status: number;
  message: string;
  field?: string;
}

// Custom error classes (imported from error-messages.ts)
export {
	NotFoundError,
	UnauthorizedError,
	ForbiddenError,
	BadRequestError,
	ConflictError,
} from '../consts/error-messages';

// Handle Sequelize-specific errors
function handleSequelizeError(error: unknown): ErrorResponse | null {
	// Unique constraint (duplicate entry)
	if (error instanceof UniqueConstraintError) {
		const field = error.errors[0]?.path || 'field';
		return {
			status: 409,
			message: `${field} already exists`,
			field,
		};
	}

	// Validation errors
	if (error instanceof ValidationError) {
		return {
			status: 400,
			message: error.errors[0]?.message || ERROR_MESSAGES.INVALID_INPUT,
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
			message: ERROR_MESSAGES.DATABASE_ERROR,
		};
	}

	return null;
}

// Handle custom application errors
function handleApplicationError(error: unknown): ErrorResponse | null {
	if (error instanceof NotFoundError) {
		return {
			status: 404,
			message: error.message,
		};
	}

	if (error instanceof UnauthorizedError) {
		return {
			status: 401,
			message: error.message,
		};
	}

	if (error instanceof ForbiddenError) {
		return {
			status: 403,
			message: error.message,
		};
	}

	if (error instanceof BadRequestError) {
		return {
			status: 400,
			message: error.message,
		};
	}

	if (error instanceof ConflictError) {
		return {
			status: 409,
			message: error.message,
		};
	}

	return null;
}

// Create a type-safe error message map
const ERROR_MESSAGE_MAP: Record<ErrorMessage, number> = {
	[ERROR_MESSAGES.USER_NOT_FOUND]: 404,
	[ERROR_MESSAGES.FARM_NOT_FOUND]: 404,
	[ERROR_MESSAGES.ANIMAL_NOT_FOUND]: 404,
	[ERROR_MESSAGES.FARM_MEMBER_NOT_FOUND]: 404,
	[ERROR_MESSAGES.MEASUREMENT_NOT_FOUND]: 404,
	[ERROR_MESSAGES.UNAUTHORIZED]: 401,
	[ERROR_MESSAGES.USER_NOT_AUTHENTICATED]: 401,
	[ERROR_MESSAGES.INVALID_CREDENTIALS]: 401,
	[ERROR_MESSAGES.TOKEN_EXPIRED]: 401,
	[ERROR_MESSAGES.FORBIDDEN]: 403,
	[ERROR_MESSAGES.INSUFFICIENT_PERMISSIONS]: 403,
	[ERROR_MESSAGES.ACCESS_DENIED]: 403,
	[ERROR_MESSAGES.INVALID_INPUT]: 400,
	[ERROR_MESSAGES.MISSING_REQUIRED_FIELD]: 400,
	[ERROR_MESSAGES.INVALID_EMAIL_FORMAT]: 400,
	[ERROR_MESSAGES.PASSWORD_TOO_WEAK]: 400,
	[ERROR_MESSAGES.INVALID_DATE_FORMAT]: 400,
	[ERROR_MESSAGES.INVALID_ID]: 400,
	[ERROR_MESSAGES.EMAIL_ALREADY_EXISTS]: 409,
	[ERROR_MESSAGES.USERNAME_ALREADY_EXISTS]: 409,
	[ERROR_MESSAGES.FARM_NAME_ALREADY_EXISTS]: 409,
	[ERROR_MESSAGES.RESOURCE_ALREADY_EXISTS]: 409,
	[ERROR_MESSAGES.INTERNAL_SERVER_ERROR]: 500,
	[ERROR_MESSAGES.DATABASE_ERROR]: 500,
	[ERROR_MESSAGES.EXTERNAL_SERVICE_ERROR]: 500,
};

// Main error handler that handles all types of errors
export function handleAllErrors(error: unknown): ErrorResponse {
	// Try Sequelize errors first
	const sequelizeError = handleSequelizeError(error);
	if (sequelizeError) {
		return sequelizeError;
	}

	// Try custom application errors
	const applicationError = handleApplicationError(error);
	if (applicationError) {
		return applicationError;
	}

	// Handle regular Error instances with type-safe message mapping
	if (error instanceof Error) {
		// Check if it's a known error message
		const errorMessage = error.message as ErrorMessage;
		const status = ERROR_MESSAGE_MAP[errorMessage];

		if (status) {
			return {
				status,
				message: errorMessage,
			};
		}

		// Fallback for unknown error messages
		console.warn('Unknown error message:', error.message);
		return {
			status: 500,
			message: ERROR_MESSAGES.INTERNAL_SERVER_ERROR,
		};
	}

	// Unknown error type
	console.error('Unknown error type:', error);
	return {
		status: 500,
		message: ERROR_MESSAGES.INTERNAL_SERVER_ERROR,
	};
}
