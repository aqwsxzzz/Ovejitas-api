import { Database } from '../database';
import { Model, ModelStatic } from 'sequelize';

// Define the structure for a single include configuration
export interface IncludeConfigItem {
  model: string; // The model name as it appears in db.models
  as: string;
  required?: boolean;
  attributes?: string[];
  nested?: IncludeConfig;
  limit?: number;
  order?: [string, 'ASC' | 'DESC'][];
}

// The main include configuration interface
export interface IncludeConfig {
  [relationName: string]: IncludeConfigItem;
}

// Sequelize include object type
export interface SequelizeIncludeObject {
  model: ModelStatic<Model>;
  as: string;
  required: boolean;
  attributes?: string[];
  include?: SequelizeIncludeObject[];
  limit?: number;
  order?: [string, 'ASC' | 'DESC'][];
}

// Type guard to ensure model exists in database
function isValidModelName(
	modelName: string,
	db: Database,
): modelName is keyof Database['models'] {
	return modelName in db.models;
}

export class IncludeParser {
	static parseIncludes(
		includeParam: string,
		allowedIncludes: IncludeConfig,
		db: Database,
	): SequelizeIncludeObject[] {

		if (!includeParam) return [];

		// Validate includes first
		this.validateIncludes(includeParam, allowedIncludes);

		const requestedIncludes = includeParam.split(',').map(i => i.trim());
		const sequelizeIncludes: SequelizeIncludeObject[] = [];

		for (const include of requestedIncludes) {
			const parts = include.split('.');
			const mainInclude = parts[0];

			// Check if the include is allowed
			if (!allowedIncludes[mainInclude]) {
				throw new Error(`Include '${mainInclude}' is not allowed`);
			}

			const config = allowedIncludes[mainInclude];

			// Validate that the model exists in the database
			if (!isValidModelName(config.model, db)) {
				throw new Error(`Model '${config.model}' does not exist in database`);
			}

			const includeObj: SequelizeIncludeObject = {
				model: db.models[config.model],
				as: config.as,
				required: config.required || false,
			};

			// Add attributes if specified
			if (config.attributes && config.attributes.length > 0) {
				includeObj.attributes = [...config.attributes]; // Create a copy to avoid mutations
			}

			// Add limit if specified
			if (config.limit !== undefined) {
				includeObj.limit = config.limit;
			}

			// Add order if specified
			if (config.order && config.order.length > 0) {
				includeObj.order = [...config.order]; // Create a copy to avoid mutations
			}

			// Handle nested includes (e.g., "translations.language")
			if (parts.length > 1 && config.nested) {
				const nestedInclude = parts.slice(1).join('.');
				includeObj.include = this.parseIncludes(nestedInclude, config.nested, db);
			}

			sequelizeIncludes.push(includeObj);
		}

		return sequelizeIncludes;
	}

	/**
   * Validates an include configuration at compile time
   * @param config - Include configuration to validate
   * @returns The same config (for chaining)
   */
	static validateConfig<T extends IncludeConfig>(config: T): T {
		// Runtime validation could be added here if needed
		return config;
	}

	/**
   * Creates a type-safe include configuration builder
   */
	static createConfig<T extends IncludeConfig>(config: T): T {
		return this.validateConfig(config);
	}

	/**
	 * Validates that an include parameter only contains allowed includes
	 * @param includeParam - The include parameter string
	 * @param allowedIncludes - Configuration of allowed includes
	 * @throws Error if any include is not allowed
	 */
	private static validateIncludes(
		includeParam: string,
		allowedIncludes: IncludeConfig,
	): void {
		const requestedIncludes = includeParam.split(',').map(i => i.trim());

		for (const include of requestedIncludes) {
			const mainInclude = include.split('.')[0];
			if (!allowedIncludes[mainInclude]) {
				throw new Error(`Include '${mainInclude}' is not allowed for this resource`);
			}
		}
	}

}

// Utility type to extract model names from Database
export type ModelName = keyof Database['models'];

// Helper type for creating strongly typed include configs
export type TypedIncludeConfig = Record<string, IncludeConfigItem & {
  model: ModelName;
}>;

