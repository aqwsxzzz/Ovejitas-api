// error-messages.ts
export const ERROR_MESSAGES = {
	// 404 Not Found
	USER_NOT_FOUND: 'User not found',
	FARM_NOT_FOUND: 'Farm not found',
	ANIMAL_NOT_FOUND: 'Animal not found',
	FARM_MEMBER_NOT_FOUND: 'Farm member not found',
	MEASUREMENT_NOT_FOUND: 'Measurement not found',

	// 401 Unauthorized
	UNAUTHORIZED: 'Unauthorized',
	USER_NOT_AUTHENTICATED: 'User not authenticated',
	INVALID_CREDENTIALS: 'Invalid email or password',
	TOKEN_EXPIRED: 'Token has expired',

	// 403 Forbidden
	FORBIDDEN: 'Forbidden',
	INSUFFICIENT_PERMISSIONS: 'Insufficient permissions',
	ACCESS_DENIED: 'Access denied',

	// 400 Bad Request
	INVALID_INPUT: 'Invalid input',
	MISSING_REQUIRED_FIELD: 'Missing required field',
	INVALID_EMAIL_FORMAT: 'Invalid email format',
	PASSWORD_TOO_WEAK: 'Password too weak',
	INVALID_DATE_FORMAT: 'Invalid date format',
	INVALID_ID: 'Invalid ID provided',

	// 409 Conflict
	EMAIL_ALREADY_EXISTS: 'Email already exists',
	USERNAME_ALREADY_EXISTS: 'Username already exists',
	FARM_NAME_ALREADY_EXISTS: 'Farm name already exists',
	RESOURCE_ALREADY_EXISTS: 'Resource already exists',

	// 500 Internal Server Error
	INTERNAL_SERVER_ERROR: 'Internal server error',
	DATABASE_ERROR: 'Database error occurred',
	EXTERNAL_SERVICE_ERROR: 'External service error',
} as const;

// Create a type from the error messages
export type ErrorMessage = typeof ERROR_MESSAGES[keyof typeof ERROR_MESSAGES];

// Success messages
export const SUCCESS_MESSAGES = {
	// General
	SUCCESS: 'Success',
	CREATED_SUCCESSFULLY: 'Created successfully',
	UPDATED_SUCCESSFULLY: 'Updated successfully',
	DELETED_SUCCESSFULLY: 'Deleted successfully',

	// Auth
	LOGIN_SUCCESSFUL: 'Login successful',
	LOGOUT_SUCCESSFUL: 'Logout successful',

	// User
	USER_CREATED: 'User created successfully',
	USER_UPDATED: 'User updated successfully',
	USER_DELETED: 'User deleted successfully',

	// Farm
	FARM_CREATED: 'Farm created successfully',
	FARM_UPDATED: 'Farm updated successfully',
	FARM_DELETED: 'Farm deleted successfully',

	// Animal
	ANIMAL_CREATED: 'Animal created successfully',
	ANIMAL_UPDATED: 'Animal updated successfully',
	ANIMAL_DELETED: 'Animal deleted successfully',
} as const;

export type SuccessMessage = typeof SUCCESS_MESSAGES[keyof typeof SUCCESS_MESSAGES];

// Helper function to create typed errors
export function createTypedError(message: ErrorMessage): Error {
	return new Error(message);
}

// Custom error classes with typed messages
export class NotFoundError extends Error {
	constructor(message: ErrorMessage = ERROR_MESSAGES.USER_NOT_FOUND) {
		super(message);
		this.name = 'NotFoundError';
	}
}

export class UnauthorizedError extends Error {
	constructor(message: ErrorMessage = ERROR_MESSAGES.UNAUTHORIZED) {
		super(message);
		this.name = 'UnauthorizedError';
	}
}

export class ForbiddenError extends Error {
	constructor(message: ErrorMessage = ERROR_MESSAGES.FORBIDDEN) {
		super(message);
		this.name = 'ForbiddenError';
	}
}

export class BadRequestError extends Error {
	constructor(message: ErrorMessage = ERROR_MESSAGES.INVALID_INPUT) {
		super(message);
		this.name = 'BadRequestError';
	}
}

export class ConflictError extends Error {
	constructor(message: ErrorMessage = ERROR_MESSAGES.RESOURCE_ALREADY_EXISTS) {
		super(message);
		this.name = 'ConflictError';
	}
}
