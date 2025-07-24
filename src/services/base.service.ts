import { Database } from '../database';
import { IncludeParser, IncludeConfig, SequelizeIncludeObject } from '../utils/include-parser';

export abstract class BaseService {
	protected db: Database;

	constructor(db: Database) {
		this.db = db;
	}

	/**
   * Parses include parameters with strict typing
   * @param includeParam - The include parameter string
   * @param allowedIncludes - Configuration of allowed includes for this service
   * @returns Array of Sequelize include objects
   */
	protected parseIncludes(
		includeParam: string | undefined,
		allowedIncludes: IncludeConfig,
	): SequelizeIncludeObject[] {
		if (!includeParam) return [];
		return IncludeParser.parseIncludes(includeParam, allowedIncludes, this.db);
	}

	/**
   * Validates that an include parameter only contains allowed includes
   * @param includeParam - The include parameter string
   * @param allowedIncludes - Configuration of allowed includes
   * @throws Error if any include is not allowed
   */
	protected validateIncludes(
		includeParam: string | undefined,
		allowedIncludes: IncludeConfig,
	): void {
		if (!includeParam) return;

		const requestedIncludes = includeParam.split(',').map(i => i.trim());

		for (const include of requestedIncludes) {
			const mainInclude = include.split('.')[0];
			if (!allowedIncludes[mainInclude]) {
				throw new Error(`Include '${mainInclude}' is not allowed for this resource`);
			}
		}
	}
}
