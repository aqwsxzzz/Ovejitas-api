import { Database } from '../database';
import { Op, WhereOptions } from 'sequelize';

// Define the structure for a single filter configuration
export interface FilterConfigItem {
  model?: string; // Optional - for nested filtering on associations
  as?: string; // For associations
  attribute: string; // The actual column/attribute to filter on
  operator?: FilterOperator; // Default operator if not specified
  type?: FilterType; // Data type for validation and conversion
  transform?: (value: string) => string | number; // Optional value transformation function
}

// Supported filter operators
export type FilterOperator =
  | 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte'
  | 'like' | 'ilike' | 'in' | 'notIn'
  | 'between' | 'notBetween'
  | 'isNull' | 'isNotNull'
  | 'contains' | 'startsWith' | 'endsWith';

// Supported filter data types
export type FilterType = 'string' | 'number' | 'boolean' | 'date' | 'uuid' | 'enum';

// The main filter configuration interface
export interface FilterConfig {
  [filterKey: string]: FilterConfigItem;
}

// Sequelize where options type
export type SequelizeWhereOptions = WhereOptions;

// Type guard to ensure model exists in database
function isValidModelName(
	modelName: string,
	db: Database,
): modelName is keyof Database['models'] {
	return modelName in db.models;
}

export class FilterParser {
	static parseFilters(
		filterParams: Record<string, string> | undefined,
		allowedFilters: FilterConfig,
		db: Database,
	): SequelizeWhereOptions {
		if (!filterParams || Object.keys(filterParams).length === 0) {
			return {};
		}

		this.validateFilters(filterParams, allowedFilters);

		const where: SequelizeWhereOptions = {};

		for (const [filterKey, filterValue] of Object.entries(filterParams)) {
			// Skip empty filter values
			if (!filterValue || filterValue.trim() === '') {
				continue;
			}

			// Parse filter key and operator (e.g., "name:like" or just "name")
			const [cleanFilterKey, operatorStr] = filterKey.split(':');

			// Check if the filter is allowed
			if (!allowedFilters[cleanFilterKey]) {
				throw new Error(`Filter '${cleanFilterKey}' is not allowed`);
			}

			const config = allowedFilters[cleanFilterKey];
			const operator = (operatorStr as FilterOperator) || config.operator || 'eq';

			// Validate operator
			if (!this.isValidOperator(operator)) {
				throw new Error(`Invalid filter operator '${operator}'`);
			}

			// Transform and validate the filter value
			const transformedValue = this.transformValue(filterValue, config, operator);

			// Build the where condition
			const condition = this.buildWhereCondition(operator, transformedValue);

			if (config.model && config.as) {
				// Validate that the model exists in the database
				if (!isValidModelName(config.model, db)) {
					throw new Error(`Model '${config.model}' does not exist in database`);
				}

				// Nested filtering (filtering on associated model)
				const associationPath = `$${config.as}.${config.attribute}$`;
				where[associationPath] = condition;
			} else {
				// Direct filtering on current model
				where[config.attribute] = condition;
			}
		}

		return where;
	}

	private static isValidOperator(operator: string): operator is FilterOperator {
		const validOperators: FilterOperator[] = [
			'eq', 'ne', 'gt', 'gte', 'lt', 'lte',
			'like', 'ilike', 'in', 'notIn',
			'between', 'notBetween',
			'isNull', 'isNotNull',
			'contains', 'startsWith', 'endsWith',
		];
		return validOperators.includes(operator as FilterOperator);
	}

	private static transformValue(
		value: string,
		config: FilterConfigItem,
		operator: FilterOperator,
	) {
		// Handle null/not null operators first
		if (operator === 'isNull' || operator === 'isNotNull') {
			return null;
		}

		// Apply custom transformation if provided
		if (config.transform) {
			return config.transform(value);
		}

		// Handle array operators (in, notIn, between)
		if (['in', 'notIn', 'between', 'notBetween'].includes(operator)) {
			const arrayValues = value.split(',').map(v => v.trim());
			return this.convertArrayValues(arrayValues, config.type || 'string');
		}

		// Convert single value based on type
		return this.convertValue(value, config.type || 'string');
	}

	private static convertValue(value: string, type: FilterType) {
		switch (type) {
		case 'number':
			const num = Number(value);
			if (isNaN(num)) {
				throw new Error(`Invalid number value: ${value}`);
			}
			return num;

		case 'boolean':
			if (!['true', 'false', '1', '0'].includes(value.toLowerCase())) {
				throw new Error(`Invalid boolean value: ${value}`);
			}
			return ['true', '1'].includes(value.toLowerCase());

		case 'date':
			const date = new Date(value);
			if (isNaN(date.getTime())) {
				throw new Error(`Invalid date value: ${value}`);
			}
			return date;

		case 'uuid':
			const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
			if (!uuidRegex.test(value)) {
				throw new Error(`Invalid UUID value: ${value}`);
			}
			return value;

		case 'enum':
		case 'string':
		default:
			return value;
		}
	}

	private static convertArrayValues(values: string[], type: FilterType) {
		return values.map(value => this.convertValue(value, type));
	}

	private static buildWhereCondition(operator: FilterOperator, value: unknown) {
		switch (operator) {
		case 'eq':
			return { [Op.eq]: value };
		case 'ne':
			return { [Op.ne]: value };
		case 'gt':
			return { [Op.gt]: value };
		case 'gte':
			return { [Op.gte]: value };
		case 'lt':
			return { [Op.lt]: value };
		case 'lte':
			return { [Op.lte]: value };
		case 'like':
			return { [Op.like]: `%${value}%` };
		case 'ilike':
			return { [Op.iLike]: `%${value}%` };
		case 'contains':
			return { [Op.like]: `%${value}%` };
		case 'startsWith':
			return { [Op.like]: `${value}%` };
		case 'endsWith':
			return { [Op.like]: `%${value}` };
		case 'in':
			return { [Op.in]: value };
		case 'notIn':
			return { [Op.notIn]: value };
		case 'between':
			if (!Array.isArray(value) || value.length !== 2) {
				throw new Error('Between operator requires exactly 2 values');
			}
			return { [Op.between]: value };
		case 'notBetween':
			if (!Array.isArray(value) || value.length !== 2) {
				throw new Error('NotBetween operator requires exactly 2 values');
			}
			return { [Op.notBetween]: value };
		case 'isNull':
			return { [Op.is]: null };
		case 'isNotNull':
			return { [Op.not]: null };
		default:
			throw new Error(`Unsupported operator: ${operator}`);
		}
	}

	/**
   * Validates a filter configuration at compile time
   * @param config - Filter configuration to validate
   * @returns The same config (for chaining)
   */
	static validateConfig<T extends FilterConfig>(config: T): T {
		// Runtime validation could be added here if needed
		return config;
	}

	/**
   * Creates a type-safe filter configuration builder
   */
	static createConfig<T extends FilterConfig>(config: T): T {
		return this.validateConfig(config);
	}

	/**
       * Validates that filter parameters only contain allowed filters
       * @param filterParams - Object containing filter parameters
       * @param allowedFilters - Configuration of allowed filters
       * @throws Error if any filter is not allowed
       */
	private static validateFilters(
		filterParams: Record<string, string> | undefined,
		allowedFilters: FilterConfig,
	): void {
		if (!filterParams) return;

		for (const filterKey of Object.keys(filterParams)) {
			const [cleanFilterKey] = filterKey.split(':');

			if (!allowedFilters[cleanFilterKey]) {
				throw new Error(`Filter '${cleanFilterKey}' is not allowed for this resource`);
			}
		}
	}

}

// Utility type to extract model names from Database
export type ModelName = keyof Database['models'];

// Helper type for creating strongly typed filter configs
export type TypedFilterConfig = Record<string, FilterConfigItem & {
  model?: ModelName;
}>;

// Helper function to create common filter configurations
export class FilterConfigBuilder {
	/**
   * Creates a basic string filter configuration
   */
	static string(attribute: string, operator: FilterOperator = 'eq'): FilterConfigItem {
		return {
			attribute,
			operator,
			type: 'string',
		};
	}

	/**
   * Creates a number filter configuration
   */
	static number(attribute: string, operator: FilterOperator = 'eq'): FilterConfigItem {
		return {
			attribute,
			operator,
			type: 'number',
		};
	}

	/**
   * Creates a boolean filter configuration
   */
	static boolean(attribute: string): FilterConfigItem {
		return {
			attribute,
			operator: 'eq',
			type: 'boolean',
		};
	}

	/**
   * Creates a date filter configuration
   */
	static date(attribute: string, operator: FilterOperator = 'eq'): FilterConfigItem {
		return {
			attribute,
			operator,
			type: 'date',
		};
	}

	/**
   * Creates an enum filter configuration
   */
	static enum(attribute: string, validValues?: string[]): FilterConfigItem {
		return {
			attribute,
			operator: 'eq',
			type: 'enum',
			transform: validValues ? (value: string) => {
				if (!validValues.includes(value)) {
					throw new Error(`Invalid enum value: ${value}. Valid values: ${validValues.join(', ')}`);
				}
				return value;
			} : undefined,
		};
	}

	/**
   * Creates a UUID filter configuration
   */
	static uuid(attribute: string): FilterConfigItem {
		return {
			attribute,
			operator: 'eq',
			type: 'uuid',
		};
	}

	/**
   * Creates a nested filter configuration for associated models
   */
	static nested(
		model: ModelName,
		as: string,
		attribute: string,
		operator: FilterOperator = 'eq',
		type: FilterType = 'string',
	): FilterConfigItem {
		return {
			model,
			as,
			attribute,
			operator,
			type,
		};
	}
}
